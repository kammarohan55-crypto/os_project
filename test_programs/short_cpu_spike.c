// short_cpu_spike.c - Brief CPU burst demonstration
// Shows short-duration high CPU usage (unlike sustained cpu_stress)

#include <stdio.h>
#include <math.h>

int main() {
    printf("[ShortCPUSpike] Starting brief CPU burst...\\n");
    fflush(stdout);
    
    // Short intense computation burst (~1 second)
    volatile double result = 0.0;
    for (long i = 0; i < 50000000; i++) {
        result += sqrt((double)i) * sin((double)i);
    }
    
    printf("[ShortCPUSpike] Burst complete (result: %g)\\n", result);
    printf("[ShortCPUSpike] Expected: Brief CPU spike, then low\\n");
    
    return 0;
}

// Compile: gcc short_cpu_spike.c -o short_cpu_spike -lm
// Expected: CPU ~80-100% for ~1 second, then drops to 0%
