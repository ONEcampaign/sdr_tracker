from scripts.update_exchange import upload_exchange

if __name__ == "__main__":
    print("Updating SDRs exchange rates")
    upload_exchange()
    print("Successfully updated SDRs exchange rates")
