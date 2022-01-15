from scripts import sdr_tracker

if __name__ == "__main__":
    # create map template for Africa
    sdr_tracker.create_africa_map_template()

    # create flourish csv
    sdr_tracker.create_sdr_map()

    print("Successfully updated SDRs Tracker")
