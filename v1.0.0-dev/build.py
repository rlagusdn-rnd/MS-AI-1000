import shutil
import os
from distutils.core import setup
from Cython.Build import cythonize

# 변환할 파일 목록
files_to_process = [
    "./BACK/backend_utils.py",
    "./BACK/MS_AI/main.py",
    "./BACK/MS_AI/nvr_utils.py",
    "./BACK/MS_AI/utils/ai_utils.py",
    "./BACK/MS_AI/utils/detect_utils.py",
    "./BACK/MS_AI/utils/flow_viz.py",
    "./BACK/MS_AI/utils/io.py",
    "./BACK/MS_AI/utils/util.py",
    "./BACK/MS_AI/models/action_classcifition_model.py",
    "./BACK/MS_AI/models/transforms.py"
]

# .pyx 파일로 변환할 파일 목록 준비
pyx_files = []

for file_path in files_to_process:
    new_file_path = file_path.replace('.py', '.pyx')
    shutil.copy(file_path, new_file_path)
    pyx_files.append(new_file_path)
    print(f"Created and deleted: {file_path} -> {new_file_path}")

# 모든 .pyx 파일을 cythonize하고 컴파일
setup(
    ext_modules=cythonize(pyx_files, compiler_directives={'language_level': "3", 'cdivision': True})
)
print("Compile Done")

build_file_middle_name = ".cpython-310-x86_64-linux-gnu.so"

for file_path in files_to_process:
    dir_path = os.path.dirname(file_path)
    new_file_name = os.path.basename(file_path).replace(".py", "") + build_file_middle_name

    cmd = f"mv ./{new_file_name} {dir_path}"
    os.system(cmd)  # 컴파일 파일 이동

for file_path in files_to_process:
    os.remove(file_path)  # 원본 .py 파일 삭제

for file_path in files_to_process:
    new_file_path = file_path.replace('.py', '.c')
    os.remove(new_file_path)  # 원본 .c 파일 삭제

for file_path in pyx_files:
    os.remove(file_path)  # 원본 .pyx 파일 삭제

