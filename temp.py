import json
import os

def convert_to_url(wlf_id):
    return f"https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId={wlf_id}"

def process_json_files():
    try:
        # 현재 스크립트의 절대 경로를 구함
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 입력/출력 디렉토리 설정
        input_dir = os.path.join(current_dir, 'backend', 'data')
        
        # 0부터 9까지의 파일 처리
        for i in range(10):
            input_file = os.path.join(input_dir, f'bokjiro_content_part{i}.json')
            output_file = os.path.join(input_dir, f'bokjiro_content_part{i}_with_url.json')
            
            # 데이터 읽기
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # ID를 URL로 변환하여 추가
            for item in data:
                if 'id' in item:
                    item['url'] = convert_to_url(item['id'])
            
            # 결과 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"처리 완료: {output_file}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    process_json_files()
