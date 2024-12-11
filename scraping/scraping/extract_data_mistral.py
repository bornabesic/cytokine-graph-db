import os
import json
import ollama
import time

def send_to_mistral(input_data):

    prompt = f"""
    You are a highly accurate extraction tool. I will provide you with the DOI of a scientific publication and its 'Data Availability' section.

    Analyze the text and extract:
    1. Accession codes (e.g., "XYZ123") or URLs from databases like GEO, ENA, or SRA.
    2. Source code URLs from GitHub or Zenodo.

    Return the results in JSON format:
    {{
        "accession codes": [list of codes or URLs],
        "source code": [list of URLs to GitHub or Zenodo]
    }}

    Input Data:
    DOI: <<DOI>> {input_data['DOI']} <<END DOI>>
    Data Availability: <<DATA>> {input_data['Data Availability']} <<END DATA>>
    """

    response = ollama.chat(model="mistral:latest", messages=[
        {
            "role": "user",
            "content": prompt
        }
    ])
    
    try:
        result = {
            "accession codes": [],
            "source code": []
        }
        
        if response and hasattr(response, 'message'):
            try:
                parsed = json.loads(response.message['content'])
                if isinstance(parsed, dict):
                    result.update(parsed)
            except json.JSONDecodeError:
                # print(f"Could not parse response as JSON: {response.message['content']}")
                parsed = {"accession codes": [], "source code": []}
                
        return result
        
    except Exception as e:
        # print(f"Error processing response: {str(e)}")
        return {
            "accession codes": [],
            "source code": []
        }

def process_json_files(directory):

    """Generalized filepath in future"""

    file_path = "_Science Bulletin_Cancer Discovery_Cell Research_udc.json"
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
        results = []
        for entry in data:
            doi = entry.get("DOI", "")
            data_availability = entry.get("paragraph", "")
            input_data = {
                "DOI": doi,
                "Data Availability": data_availability
            }
            print('Processing DOI:', doi)

            try:
                # start_time = time.time()
                result = send_to_mistral(input_data)
                # end_time = time.time()
                # print("Execution time:", end_time-start_time)
                results.append({
                    "DOI": doi,
                    "results": result
                })
                # print(f"Processed entry. Result: {result}")
            except Exception as e:
                print(f"Error processing DOI {doi}: {str(e)}")
        
        # print(results)
        # Save results to output file
        output_file = "extraction_results_mistral_sciBulletin.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)

if __name__ == "__main__":
    json_directory = os.path.dirname(os.path.abspath(__file__))
    process_json_files(json_directory)