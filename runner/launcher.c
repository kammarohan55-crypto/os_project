#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <sys/mount.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <time.h>
#include "../policies/seccomp_rules.h"
#include "telemetry.h"

// Stack size for cloned child
#define STACK_SIZE (1024 * 1024)

/**
 * STRUCTURE:
 * 1. Parse Arguments (Binary to run)
 * 2. Setup Resources (RLIMIT)
 * 3. Isolate (Namespaces) - handled via 'unshare' or 'clone' logic
 * 4. Apply Seccomp
 * 5. Execve
 */

struct container_config {
    char *binary_path;
    char **args;
    sandbox_profile_t profile;
};

// Child process function
int child_fn(void *arg) {
    struct container_config *config = (struct container_config *)arg;

    printf("[Sandbox-Child] PID: %d inside new namespace\n", getpid());

    // -------------------------------------------------------------
    // F. INTERPROCESS COMMUNICATION (IPC)
    // Mechanism: IPC Isolation via Namespace
    // The child is in a new IPC namespace, so it cannot see host semaphores/shm.
    // -------------------------------------------------------------
    
    // -------------------------------------------------------------
    // E. FILE SYSTEM MANAGEMENT
    // Mechanism: Mount Namespace + Read-Only Root
    // -------------------------------------------------------------
    // 1. make mount setting private
    if (mount(NULL, "/", NULL, MS_PRIVATE | MS_REC, NULL) != 0) {
        perror("mount / private");
    }
    
    // 2. Remount / as Read-Only
    // This prevents the untrusted process from modifying ANY file in the system
    // unless we explicitly mount a writable tmpfs (which we skip for strict sandbox).
    if (mount(NULL, "/", NULL, MS_REMOUNT | MS_BIND | MS_RDONLY, NULL) != 0) {
       perror("mount / read-only");
       // Non-fatal for demo if unprivileged, but critical for security.
    } else {
       printf("[Sandbox-Child] Filesystem locked (Read-Only Root Enforced).\n");
    }
    
    // -------------------------------------------------------------
    // B. MEMORY MANAGEMENT (Soft Limits)
    // Mechanism: setrlimit() for Stack and Data
    // Hard limits are enforced by Cgroups v2 in the Python runner (or here if Resource Aware).
    // -------------------------------------------------------------
    if (config->profile == PROFILE_RESOURCE_AWARE) {
         // Tighter limits or specific ones for Resource Aware
         printf("[Sandbox-Child] Applying RESOURCE-AWARE limits...\n");
    }

    struct rlimit rl;
    // Limit stack to 8MB
    rl.rlim_cur = 8 * 1024 * 1024;
    rl.rlim_max = 8 * 1024 * 1024;
    setrlimit(RLIMIT_STACK, &rl);

    // Limit File Descriptors
    rl.rlim_cur = 64;
    rl.rlim_max = 64;
    setrlimit(RLIMIT_NOFILE, &rl);

    // B. MEMORY MANAGEMENT (Fallback if Cgroups fail)
    // Limit Address Space to 128MB
    rl.rlim_cur = 128 * 1024 * 1024;
    rl.rlim_max = 128 * 1024 * 1024;
    setrlimit(RLIMIT_AS, &rl);
    
    // C. PROCESS MANAGEMENT (Fallback)
    // Limit number of processes (Fork Bomb protection)
    // Note: In unprivileged UserNS, this limits processes in this namespace.
    rl.rlim_cur = 20;
    rl.rlim_max = 20;
    setrlimit(RLIMIT_NPROC, &rl);

    // -------------------------------------------------------------
    // D. SYSTEM CALL HANDLING
    // Mechanism: Seccomp BPF
    // -------------------------------------------------------------
    install_syscall_filter(config->profile);

    // -------------------------------------------------------------
    // C. PROCESS MANAGEMENT
    // Mechanism: execv()
    // Replaces the current process image with the untrusted code.
    // -------------------------------------------------------------
    printf("[Sandbox-Child] Executing untrusted binary: %s\n", config->binary_path);
    execv(config->binary_path, config->args);

    // If execv returns, it failed
    perror("execv failed");
    return 1;
}

void print_usage(const char *prog) {
    fprintf(stderr, "Usage: %s [--profile=STRICT|RESOURCE-AWARE|LEARNING] <executable> [args...]\n", prog);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    // Default profile
    sandbox_profile_t profile = PROFILE_STRICT;
    char *profile_str = "STRICT";
    
    int bin_index = 1;
    if (strncmp(argv[1], "--profile=", 10) == 0) {
        char *pinfo = argv[1] + 10;
        if (strcmp(pinfo, "STRICT") == 0) {
            profile = PROFILE_STRICT;
            profile_str = "STRICT";
        } else if (strcmp(pinfo, "RESOURCE-AWARE") == 0) {
            profile = PROFILE_RESOURCE_AWARE;
            profile_str = "RESOURCE-AWARE";
        } else if (strcmp(pinfo, "LEARNING") == 0) {
            profile = PROFILE_LEARNING;
            profile_str = "LEARNING";
        } else {
             fprintf(stderr, "Unknown profile: %s. Using STRICT.\n", pinfo);
        }
        bin_index++;
    }

    if (bin_index >= argc) {
        print_usage(argv[0]);
        return 1;
    }

    printf("[Sandbox-Parent] Preparing execution environment (Profile: %s)...\n", profile_str);
    
    // Ensure logs directory exists
    ensure_logs_directory();

    // Prepare child stack
    char *stack = malloc(STACK_SIZE);
    if (!stack) {
        perror("malloc stack");
        exit(1);
    }
    
    // Setup config
    struct container_config config;
    config.binary_path = argv[bin_index];
    config.args = &argv[bin_index]; // Pass the executable + its args
    config.profile = profile;

    // -------------------------------------------------------------
    // C. PROCESS MANAGEMENT & E. FILESYSTEM
    // Mechanism: clone() with CLONE_NEW* flags
    // Creating a new process in new namespaces (PID, IPC, UTS, MOUNT).
    // SIGCHLD tells the kernel to notify us when child dies.
    // -------------------------------------------------------------
    // Note: Creating User Namespaces (CLONE_NEWUSER) allows unprivileged users 
    // to usage other namespaces. Required for WSL2 often.
    
    int flags = CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWIPC | CLONE_NEWUTS | CLONE_NEWUSER | SIGCHLD;
    
    long start_time = get_current_time_ms();
    
    pid_t child_pid = clone(child_fn, stack + STACK_SIZE, flags, &config);

    
    if (child_pid == -1) {
        perror("clone failed (Trying fallback to simple fork without namespaces if unprivileged)");
        exit(1);
    }

    printf("[Sandbox-Parent] Child launched with PID: %d\n", child_pid);

    // -------------------------------------------------------------
    // H. TIME MANAGEMENT & TELEMETRY
    // Mechanism: waitpid(WNOHANG) + Polling
    // -------------------------------------------------------------
    int status;
    int child_running = 1;
    
    telemetry_log_t log_data = {0};
    log_data.program_name = config.binary_path;
    log_data.profile_name = profile_str;
    log_data.cpu_usage_percent = 0;
    log_data.memory_peak_kb = 0;
    log_data.minflt = 0;
    log_data.majflt = 0;
    log_data.read_syscalls = 0;
    log_data.write_syscalls = 0;
    log_data.blocked_syscalls = 0;
    log_data.samples = NULL;
    log_data.sample_count = 0;
    
    unsigned long long total_ticks = 0;
    
    // CPU Usage Tracking (Delta-based calculation)
    // We need previous measurements to compute CPU% over time intervals
    unsigned long long prev_process_ticks = 0;
    unsigned long long prev_total_ticks = 0;
    int num_cores = sysconf(_SC_NPROCESSORS_ONLN);
    if (num_cores <= 0) num_cores = 1;  // Fallback if sysconf fails


    // Monitoring Loop
    while (child_running) {
        pid_t result = waitpid(child_pid, &status, WNOHANG);
        
        if (result == 0) {
            // Child still running, collect metrics
            long current_mem = get_memory_peak(child_pid);
            if (current_mem > log_data.memory_peak_kb) {
                log_data.memory_peak_kb = current_mem;
            }
            
            // Capure CPU ticks and Faults
            unsigned long minflt = 0, majflt = 0;
            unsigned long long current_ticks = get_process_metrics(child_pid, &minflt, &majflt);
            if (current_ticks > total_ticks) {
                total_ticks = current_ticks;
            }
            // Update faults (they are cumulative in stat, so just take latest)
            log_data.minflt = minflt;
            log_data.majflt = majflt;
            
            // Collect I/O syscall counts from /proc/[pid]/io
            // These represent read/write syscall activity during process execution.
            // Captured at same sampling interval as CPU/memory (100ms).
            unsigned long read_sc = 0, write_sc = 0;
            get_io_syscalls(child_pid, &read_sc, &write_sc);
            // Store the latest values (they are cumulative, so we keep the current snapshot)
            log_data.read_syscalls = read_sc;
            log_data.write_syscalls = write_sc;
            
            /*
             * CPU Usage Calculation (Delta-Based, Multi-Core Aware)
             * 
             * Data Sources:
             *   - Process ticks: /proc/[pid]/stat (utime + stime)
             *   - Total system ticks: /proc/stat (sum of all CPU time fields)
             *   - Number of cores: sysconf(_SC_NPROCESSORS_ONLN)
             * 
             * Formula:
             *   delta_process = current_process_ticks - prev_process_ticks
             *   delta_total   = current_system_ticks - prev_system_ticks
             *   CPU% = (delta_process / delta_total) × 100 × num_cores
             * 
             * Why this works:
             *   - delta_process/delta_total = fraction of total CPU time used
             *   - Multiplying by num_cores normalizes to per-core percentage
             *   - Single-threaded 100% busy process → 100% (matches top/htop)
             * 
             * Edge cases:
             *   - First sample: No prev data → CPU% = 0
             *   - delta_total == 0: Should never happen with 100ms sampling
             */
            unsigned long long current_total_ticks = get_system_cpu_ticks();
            int current_cpu_percent = 0;
            
            if (prev_total_ticks > 0) {
                // We have previous data, can calculate delta
                unsigned long long process_delta = current_ticks - prev_process_ticks;
                unsigned long long total_delta = current_total_ticks - prev_total_ticks;
                
                if (total_delta > 0) {
                    // Calculate: (process_cpu / total_cpu) * 100 * num_cores
                    current_cpu_percent = (int)((process_delta * 100 * num_cores) / total_delta);
                    
                    // Sanity check: cap at (num_cores * 100)% in case of measurement errors
                    int max_cpu = num_cores * 100;
                    if (current_cpu_percent > max_cpu) {
                        current_cpu_percent = max_cpu;
                    }
                }
            }
            // Else: first sample, keep current_cpu_percent = 0
            
            // Update previous readings for next iteration
            prev_process_ticks = current_ticks;
            prev_total_ticks = current_total_ticks;
            
            // Add time-series sample
            long elapsed = get_current_time_ms() - start_time;
            add_sample(&log_data, elapsed, current_cpu_percent, current_mem);

            // -------------------------------------------------------------
            // DYNAMIC POLICY ADAPTATION (Phase 5)
            // OS Concept: Runtime Enforcement based on Behavioral Analysis
            // -------------------------------------------------------------
            if (config.profile == PROFILE_LEARNING) {
                // Heuristic: If CPU ticks > Threshold or Faults > Threshold
                // In a real system, this would be more complex or use eBPF data
                
                // Thresholds (Arbitrary for demo)
                unsigned long long cpu_threshold_ticks = sysconf(_SC_CLK_TCK) * 2; // ~2 seconds of full CPU
                unsigned long fault_threshold = 1000;
                
                if (current_ticks > cpu_threshold_ticks || majflt > fault_threshold) {
                     printf("\n[Sandbox-Monitor] ⚠️ RISK DETECTED in Learning Mode!\n");
                     printf("[Sandbox-Monitor] Reason: usage (%llu ticks) or faults (%lu) > threshold.\n", current_ticks, majflt);
                     printf("[Sandbox-Monitor] 🔄 ADAPTING POLICY: Switching to STRICT enforcement (Terminating Process)...\n");
                     
                     kill(child_pid, SIGKILL);
                     child_running = 0;
                     
                     snprintf(log_data.exit_reason, sizeof(log_data.exit_reason), "POLICY_ADAPATION_KILL");
                }
            }


            
            usleep(100000); // 100ms sample rate
        } else if (result == -1) {
            perror("waitpid");
            child_running = 0;
        } else {
            // Child exited
            child_running = 0;
        }
    }
    
    long end_time = get_current_time_ms();
    log_data.runtime_ms = end_time - start_time;

    /*
     * Final CPU Usage Summary
     * 
     * We take the peak CPU% from all the timeline samples.
     * This is more accurate than trying to compute an overall average
     * because the delta-based calculation in the monitoring loop already
     * provides correct instantaneous CPU% values.
     * 
     * The peak_cpu value represents the maximum CPU usage observed
     * during any 100ms sampling interval during the process lifetime.
     */
    if (log_data.sample_count > 0) {
        // Find peak CPU from timeline samples
        int peak = 0;
        for (int i = 0; i < log_data.sample_count; i++) {
            if (log_data.samples[i].cpu_percent > peak) {
                peak = log_data.samples[i].cpu_percent;
            }
        }
        log_data.cpu_usage_percent = peak;
    } else {
        // No samples collected (process exited too quickly)
        log_data.cpu_usage_percent = 0;
    }


    if (WIFEXITED(status)) {
        printf("[Sandbox-Parent] Child exited with status: %d\n", WEXITSTATUS(status));
        snprintf(log_data.exit_reason, sizeof(log_data.exit_reason), "EXITED(%d)", WEXITSTATUS(status));
    } else if (WIFSIGNALED(status)) {
        int sig = WTERMSIG(status);
        printf("[Sandbox-Parent] Child killed by signal: %d\n", sig);
        snprintf(log_data.termination_signal, sizeof(log_data.termination_signal), "SIG%d", sig);
        
        if (sig == SIGSYS) {
             printf("[Sandbox-Parent] DETECTED ILLEGAL SYSCALL (Seccomp Blocked)\n");
             snprintf(log_data.exit_reason, sizeof(log_data.exit_reason), "SECURITY_VIOLATION");
             // In a real audit setup, we'd read audit log to find WHICH syscall. 
             // Here we assume based on context or store "Unknown"
             snprintf(log_data.blocked_syscall, sizeof(log_data.blocked_syscall), "Unknown(SIGSYS)");
             // Increment counter for blocked syscalls (only one detected per run in this model)
             log_data.blocked_syscalls = 1;
        } else if (sig == SIGKILL) {
             snprintf(log_data.exit_reason, sizeof(log_data.exit_reason), "KILLED_BY_OS");
        } else {
             snprintf(log_data.exit_reason, sizeof(log_data.exit_reason), "SIGNALED");
        }
    }
    
    // Generate Log Filename with PID for uniqueness
    char filename[128];
    snprintf(filename, sizeof(filename), "logs/run_%d_%ld.json", child_pid, time(NULL));
    log_telemetry(filename, &log_data, child_pid);

    free(stack);
    return 0;
}

