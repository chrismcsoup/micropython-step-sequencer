"""
File system test - write and read operations
"""
import os

def test_file_operations():
    test_file = "test_data.txt"
    test_content = "Hello from MicroPython!\nLine 2: Testing file I/O\nLine 3: 123456"
    
    print("=== File System Test ===")
    
    # Check if file already exists
    file_exists = False
    try:
        os.stat(test_file)
        file_exists = True
    except OSError:
        pass
    
    if file_exists:
        print(f"\nFile {test_file} already exists!")
        print("Reading existing content...")
        try:
            with open(test_file, 'r') as f:
                existing_content = f.read()
            print("-" * 40)
            print(existing_content)
            print("-" * 40)
        except Exception as e:
            print(f"   Read failed: {e}")
        return
    
    # Write to file
    print(f"\n1. Writing to {test_file}...")
    try:
        with open(test_file, 'w') as f:
            f.write(test_content)
        print("   Write successful")
    except Exception as e:
        print(f"   Write failed: {e}")
        return
    
    # Read from file
    print(f"\n2. Reading from {test_file}...")
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        print("   Read successful")
        print(f"\n3. Content read from file:")
        print("-" * 40)
        print(content)
        print("-" * 40)
    except Exception as e:
        print(f"   Read failed: {e}")
        return
    
    # Verify content matches
    print("\n4. Verifying content...")
    if content == test_content:
        print("   Content matches!")
    else:
        print("   Content mismatch!")
        print(f"   Expected: {test_content}")
        print(f"   Got: {content}")
    
    # Append to file
    print(f"\n5. Appending to {test_file}...")
    try:
        with open(test_file, 'a') as f:
            f.write("\nLine 4: Appended text")
        print("   Append successful")
    except Exception as e:
        print(f"   Append failed: {e}")
        return
    
    # Read again
    print(f"\n6. Reading after append...")
    try:
        with open(test_file, 'r') as f:
            final_content = f.read()
        print("   Read successful")
        print(f"\n7. Final content:")
        print("-" * 40)
        print(final_content)
        print("-" * 40)
    except Exception as e:
        print(f"   Read failed: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_file_operations()
