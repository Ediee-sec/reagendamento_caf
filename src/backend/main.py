from backend.ws_extract_file import WSExtractFile

if __name__ == '__main__':
    job = WSExtractFile()
    job.login()
    job.navegation()
    job.filter() 
    job.reschedule()
