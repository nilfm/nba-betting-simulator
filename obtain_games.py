import get_data
import process_data

def main():
    print("Requesting the data from the API")
    get_data.write_to_file()
    print("Processing the data")
    process_data.daily_save()

if __name__ == '__main__':
    main()
