import arxiv
import requests
from bs4 import BeautifulSoup
import re
import os
import tarfile
import json
from datetime import datetime
import shutil
import time

def format_ss_date_to_iso(pub_date, year):
    if pub_date: 
        try:
            dt = datetime.strptime(pub_date, '%Y-%m-%d')
            return dt.isoformat()
        except ValueError:
            pass 
            
    if year: 
        return f"{year}-01-01T00:00:00"
    
    return None 


def create_references_json(base_id, paper_output_dir):
    print(f"Lấy tham khảo cho {base_id}")
    
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{base_id}"
    fields = "references,references.externalIds,references.title,references.authors,references.publicationDate,references.year,references.paperId"
    params = {"fields": fields}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    references_dict = {}
    max_retries = 3
    retry_count = 0
    data = None
    
    time.sleep(3.1) 
    while retry_count < max_retries:
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status() 
            data = response.json()
            print(f"    Lấy API thành công cho {base_id}.")
            break 

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_count += 1
                
                wait_time = 305 
                
                print(f"    [LỖI 429] Đã đạt giới hạn. Đang ngủ {wait_time} giây... (Thử lại {retry_count}/{max_retries})")
                time.sleep(wait_time)
            
            else:
                print(f"  [Lỗi HTTP] Không thể lấy tham khảo cho {base_id}: {e}")
                break 
                
        except Exception as e:
            print(f"  [Lỗi] trong Phần 3 (Semantic Scholar): {e}")
            break 

    # Lọc và Định dạng Dữ liệu
    if data:
        if "references" not in data or not data["references"]:
            print(f"    {base_id} không có dữ liệu tham khảo.")
        else:
            for ref in data["references"]:
                if not ref or "externalIds" not in ref or not ref["externalIds"]:
                    continue 

                if "ArXiv" in ref["externalIds"]:
                    arxiv_id_raw = ref["externalIds"]["ArXiv"]
                    
                    if not arxiv_id_raw or not isinstance(arxiv_id_raw, str):
                        continue
                        
                    try:
                        yymm = arxiv_id_raw.split('.')[0]
                        id_part = arxiv_id_raw.split('.')[1]
                        if not yymm.isdigit() or len(yymm) != 4: 
                           continue 
                        
                        key_id = f"{yymm}-{id_part}"
                    except Exception:
                        continue 

                    title = ref.get("title")
                    authors = [author.get("name") for author in ref.get("authors", []) if author.get("name")]
                    submission_date = format_ss_date_to_iso(ref.get("publicationDate"), ref.get("year"))
                    ss_id = ref.get("paperId") 

                    references_dict[key_id] = {
                        "title": title,
                        "authors": authors,
                        "submission_date": submission_date,
                        "SemanticScholar_ID": ss_id
                    }
            
            print(f"    Tìm thấy và xử lý {len(references_dict)} tham khảo có arXiv ID.")

    # Ghi tệp `references.json`
    ref_path = os.path.join(paper_output_dir, "references.json")
    with open(ref_path, 'w', encoding='utf-8') as f:
        json.dump(references_dict, f, indent=4, ensure_ascii=False)
    print(f"  Đã ghi {ref_path}")

if __name__ == "__main__":
    
    STUDENT_ID = "23120266" 
    
    # Danh sách ID bài báo được giao
    PAPER_IDS_TO_SCRAPE_P1 = [f"2410.{i:05d}" for i in range(19448, 99999)] 
    PAPER_IDS_TO_SCRAPE_P2 = [f"2411.{i:05d}" for i in range(1, 221)]
    
    # Tạo thư mục gốc dựa trên MSSV
    os.makedirs(STUDENT_ID, exist_ok=True)
    
    # Xử lý từng bài báo
    for paper_id in PAPER_IDS_TO_SCRAPE_P2:
        #if not process_paper(paper_id, STUDENT_ID): 
        #    break 
        formatted_id = paper_id.replace('.', '-')
        paper_output_dir = os.path.join(STUDENT_ID, formatted_id)
        create_references_json(paper_id, paper_output_dir) 

    for paper_id in PAPER_IDS_TO_SCRAPE_P1:
        # if not process_paper(paper_id, STUDENT_ID): 
        #    break
        formatted_id = paper_id.replace('.', '-')
        paper_output_dir = os.path.join(STUDENT_ID, formatted_id)
        create_references_json(paper_id, paper_output_dir) 

    # Dọn dẹp thư mục tải về tạm thời
    if os.path.exists("./temp_downloads"):
        shutil.rmtree("./temp_downloads")