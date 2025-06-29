python ./extract_todos.py

if [ $? -eq 0 ]; then
    python ./create_issues.py 
    if [ $? -eq 0 ]; then
        echo "Issues created successfully."
    else
        echo "Error creating issues."
        exit 1
    fi
else
    echo "Error extracting TODOs."
    exit 1
fi  
  