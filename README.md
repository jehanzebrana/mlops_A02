MLOPS_Assignment02: Data Preprocessing Workflow
Overview
This repository presents a Python script and an Apache Airflow DAG designed to automate the extraction and preprocessing of data from the BBC News website. Below is an outline of the workflow and the hurdles encountered during implementation.

Workflow Summary
Data Extraction:
The script utilizes BeautifulSoup and requests libraries to scrape headlines and descriptions from the BBC News homepage.

Text Preprocessing:
Text preprocessing is executed through a preprocess_text function, which cleans and formats the extracted text data.

Data Storage and Version Control:
Preprocessed data is stored in a CSV file, and Data Version Control (DVC) is implemented to track versions and ensure reproducibility.

Apache Airflow DAG Development:
An Airflow DAG named assignment_dag is created to automate the data extraction, preprocessing, push to dvc and github.

Challenges Faced
Apache Airflow Installation: Difficulties were encountered during Apache Airflow installation due to compatibility issues and system dependencies.
Automating git operations within Airflow tasks without manual intervention.
Dealing with relative URLs and converting them to absolute.


Conclusion
Combining Apache Airflow, DVC, and GitHub creates a powerful system for orchestrating data pipelines. This setup guarantees efficient, dependable, and transparent processes for data extraction, transformation, and loading. The project underscores the critical roles of data quality, automation, and version control in contemporary data engineering.
