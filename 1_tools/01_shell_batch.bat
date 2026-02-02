
md "shell_test"

echo print("hello world, I'm batch.") > test_print.py

ren test_print.py new_test_print.py

icacls *

python new_test_print.py

#rd shell_test

pause