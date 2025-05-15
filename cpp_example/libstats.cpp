#include <vector>
#include <numeric>
#include <cmath>

// Export symbols for shared library
#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif

extern "C" {
    // Calculate mean of a vector of doubles
    EXPORT double calculate_mean(const double* data, size_t size) {
        if (size == 0) return 0.0;
        
        double sum = 0.0;
        for (size_t i = 0; i < size; ++i) {
            sum += data[i];
        }
        
        return sum / static_cast<double>(size);
    }
    
    // Calculate standard deviation of a vector of doubles
    EXPORT double calculate_stddev(const double* data, size_t size, bool sample = true) {
        if (size <= 1) return 0.0;
        
        double mean = calculate_mean(data, size);
        double sum_squared_diff = 0.0;
        
        for (size_t i = 0; i < size; ++i) {
            double diff = data[i] - mean;
            sum_squared_diff += diff * diff;
        }
        
        // Use n-1 for sample standard deviation (Bessel's correction)
        double divisor = sample ? static_cast<double>(size - 1) : static_cast<double>(size);
        return std::sqrt(sum_squared_diff / divisor);
    }
    
    // Calculate median of a vector of doubles
    EXPORT double calculate_median(double* data, size_t size) {
        if (size == 0) return 0.0;
        
        // Sort the data (note: this modifies the input array)
        std::sort(data, data + size);
        
        if (size % 2 == 0) {
            // Even number of elements, average the middle two
            return (data[size/2 - 1] + data[size/2]) / 2.0;
        } else {
            // Odd number of elements, return the middle one
            return data[size/2];
        }
    }
}