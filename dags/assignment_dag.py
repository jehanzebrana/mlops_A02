import os
import requests
import csv
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
from airflow.operators.bash import BashOperator


# Define the source websites for extraction
sources = ['https://www.dawn.com/', 'https://www.bbc.com/']
csv_path = os.path.join(os.getcwd(), 'output.csv')

def extract():
    """Extract titles, descriptions, and hrefs from specified sources with unique IDs."""
    data = []
    id_counter = 1  # Start an ID counter at 1

    def fetch_and_process(href, id_counter):
        # Check if the href is a relative URL and convert to absolute if necessary
        if href.startswith('/'):
            href = urljoin(source, href)  # source is defined in the for loop below

        try:
            page_req = requests.get(href)
            page_soup = BeautifulSoup(page_req.text, 'html.parser')

            # Extract title directly from the <title> tag of the linked page
            title_tag = page_soup.find('title')
            title = title_tag.text.strip() if title_tag else "No title available"

            # Extract description from the <meta name="description"> tag of the linked page
            description_tag = page_soup.find('meta', attrs={'name': 'description'})
            description = description_tag['content'].strip() if description_tag and 'content' in description_tag.attrs else "No description available"

            return (id_counter, title, description, href)

        except requests.RequestException as e:
            logging.error(f"Error fetching data from {href}: {e}")

    for source in sources:
        try:
            source_req = requests.get(source)
            source_soup = BeautifulSoup(source_req.text, 'html.parser')

            links = source_soup.find_all('a', href=True)  # Get all links
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(fetch_and_process, link['href'], i) for i, link in enumerate(links, start=id_counter)]
                for future in futures:
                    result = future.result()
                    if result:
                        data.append(result)

            id_counter += len(links)  # Update the ID counter based on the number of links processed

        except requests.RequestException as e:
            logging.error(f"Error fetching data from {source}: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    return data

def transform(**kwargs):
    ti = kwargs['ti']
    extracted_data = ti.xcom_pull(task_ids='extract')
    if not extracted_data:
        logging.info("No data received from extract")
        return []

    # Initialize transformed data list
    transformed_data = []

    # Iterate through each article's data
    for id, title, description, href in extracted_data:
        # Strip leading and trailing spaces from title and description
        clean_title = title.strip() if title else "No title available"
        clean_description = description.strip() if description else "No description available"

        # Append the cleaned data along with other details to the transformed data list
        transformed_data.append((id, clean_title, clean_description, href))

    return transformed_data

def load(**kwargs):
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='transform')
    if data is None:
        logging.error("No data to load.")
        return

    csv_path = os.path.join(os.getcwd(), 'output.csv')
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Title', 'Description', 'URL'])  # Write the header
        for row in data:
            writer.writerow(row)
    
    logging.info(f"Data successfully saved to {csv_path}")  # Logs the full path to the CSV

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 12),
    'email': ['i200704@nu.edu.pk'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'assignment_dag',
    default_args=default_args,
    description='Task of assignment',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# Define tasks using PythonOperator
t1 = PythonOperator(
    task_id='data',
    python_callable=extract,
    dag=dag
)

t2 = PythonOperator(
    task_id='data-transform',
    python_callable=transform,
    provide_context=True,
    dag=dag
)

t3 = PythonOperator(
    task_id='data-load',
    python_callable=load,
    provide_context=True,
    dag=dag
)

dvcpush = BashOperator(
    task_id='dvc',
    bash_command="cd $(dirname {}) && dvc add output.csv && dvc commit output.csv -f && dvc push".format(csv_path),
    dag=dag
)

gitpush = BashOperator(
    task_id='github',
    bash_command="""
    cd $(dirname {}) && \
    git add .dvc/config output.csv.dvc .gitignore && \
    git diff --staged --quiet || git commit -m 'Add DVC files' && \
    git push -u origin main
    """.format(csv_path),
    dag=dag
)

t1 >> t2 >> t3 >> dvcpush >> gitpush
