from local_test_esg import test_esg_indicators
from local_test_advice import test_advice
from local_test_indicators import test_overlap_studies_cases, test_volumes_cases
from local_test_indicators import test_momentums_cases, test_cycles_cases
from local_test_indicators import test_price_transforms_cases, test_volatilitys_cases
from local_test_indicators import test_pattern_recognition_cases, test_statistical_functions_cases
if __name__ == "__main__":
    try:
        test_esg_indicators()
        test_advice()
        test_overlap_studies_cases()
        test_momentums_cases()
        test_volumes_cases()
        test_cycles_cases()
        test_price_transforms_cases()
        test_volatilitys_cases()
        test_pattern_recognition_cases()
        test_statistical_functions_cases()
        print('\x1b[6;30;42m' + 'ALL TESTS PASSED!' + '\x1b[0m')
    except Exception as e:
        print(f"Error: {e}")
        print('FAILED TESTS')
