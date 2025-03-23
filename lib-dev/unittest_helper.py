def create_filtered_test_case(test_path):
    """
    Create a filtered test case from a path string like 'module.TestClass.test_method'.
    The method part is optional.

    Returns: A new test case class that only contains the specified test method or
    all test methods if no specific method is requested
    """
    parts = test_path.split(".")

    if len(parts) < 2:
        raise ValueError(
            "Invalid test path format. Use 'module.TestClass' or 'module.TestClass.test_method'"
        )

    module_name = parts[0]
    class_name = parts[1]
    target_method_name = parts[2] if len(parts) >= 3 else None

    # Import the module
    module = __import__(module_name)
    # Get the test class
    original_test_class = getattr(module, class_name)

    # If no specific test method requested, return the original class
    if not target_method_name:
        return original_test_class

    # Find all test methods
    test_methods = [
        name
        for name in dir(original_test_class)
        if name.startswith("test_") and callable(getattr(original_test_class, name))
    ]

    # Check if the specified test method exists
    if target_method_name not in test_methods:
        available_methods = ", ".join(test_methods)
        raise ValueError(
            f"Test method '{target_method_name}' not found in {class_name}. Available test methods: {available_methods}"
        )

    # Create a subclass with the filtered test methods
    class FilteredTestCase(original_test_class):
        __name__ = original_test_class.__name__

    # Replace all non-target test methods with no-op functions
    for method_name in test_methods:
        if method_name != target_method_name:
            # delete the method from the class
            delattr(original_test_class, method_name)

    return FilteredTestCase
