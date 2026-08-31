#!/usr/bin/env python3
"""
공백이 포함된 라벨링 데이터 폴더 이름을 수정하는 스크립트
"""
import os
from pathlib import Path

# 수정할 이벤트 타입 리스트
EVENT_TYPES = ["침입 ", "배회 ", "쓰러짐 ", "방화 ", "싸움 ", "무단투기 "]

def fix_folder_names(base_path):
    """공백이 포함된 폴더 이름을 수정"""
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"경로가 존재하지 않습니다: {base_path}")
        return
    
    renamed_count = 0
    
    # 모든 하위 폴더를 재귀적으로 탐색 (깊이 우선)
    for root, dirs, files in os.walk(base_path, topdown=False):
        for dir_name in dirs:
            # 각 이벤트 타입에 대해 공백 포함 여부 확인
            for event_type in EVENT_TYPES:
                if event_type in dir_name:
                    old_path = Path(root) / dir_name
                    new_name = dir_name.replace(event_type, event_type.strip())
                    new_path = Path(root) / new_name
                    
                    if old_path != new_path:
                        try:
                            print(f"변경: {old_path.relative_to(base_path)} -> {new_name}")
                            old_path.rename(new_path)
                            renamed_count += 1
                        except Exception as e:
                            print(f"오류: {old_path} - {e}")
                    break
    
    print(f"\n총 {renamed_count}개의 폴더 이름이 수정되었습니다.")

if __name__ == "__main__":
    base_path = "/root/backup/workspace/MS-AI-1000/backup/dataset/auto_labeled_data"
    print(f"라벨링 데이터 폴더 이름 수정 시작: {base_path}\n")
    fix_folder_names(base_path)
    print("\n완료!")

