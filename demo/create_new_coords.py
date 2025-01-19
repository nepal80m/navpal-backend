import csv

with open("coords_adjust.txt", 'r') as f:
    lat_adj, lng_adj = [float(line.strip()) for line in f]



input_csv = "coords_real.csv"
output_csv = "coords_adjusted.csv"

with open(input_csv, mode='r') as infile, open(output_csv, mode='w', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    # Read and write the header
    header = next(reader)
    writer.writerow(header)

    for row in reader:
        # Assuming the columns to modify are the first and second columns
        row[0] = str(float(row[0]) - lat_adj)  # Add to first column
        row[1] = str(float(row[1]) - lng_adj)  # Add to second column
        writer.writerow(row)
