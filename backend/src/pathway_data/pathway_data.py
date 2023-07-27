import os
import requests
import argparse
import pandas as pd
import csv
import kegg
import sys
import datetime

sys.path.append("..")
import util.data_util as util


def parse_cli_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "species_name",
        type=str,
        help="Species name (e.g. Homo sapiens / human)",
    )

    return parser.parse_args()


def download_data(species):
    """
    Downloads the data from Baderlabs

    Arguments:
    species: the species which data we want to download
    """

    if species.lower() == "mouse":
        url = "http://download.baderlab.org/EM_Genesets/current_release/Mouse/UniProt/Mouse_GO_AllPathways_with_GO_iea_July_03_2023_UniProt.gmt"

    elif species.lower() == "human":
        url = "http://download.baderlab.org/EM_Genesets/current_release/Human/UniProt/Human_GO_AllPathways_with_GO_iea_July_03_2023_UniProt.gmt"

    else:
        return "Invalid species."

    response = requests.get(url)
    with open(f"{species}_AllPathways.gmt", "wb") as file:
        file.write(response.content)
    return 1


def read_data(file_name):
    """
    Reads the data from the specified file and returns it as a DataFrame.

    Arguments:
    file_name: the name of the file to read
    """
    with open(file_name, "r") as file:
        reader = csv.reader(file, delimiter="\t")
        data = []
        for row in reader:
            name = row[0].split("%")
            source = name[1]
            id = name[2]
            descr = row[1]
            proteins = ",".join(row[2:])
            data.append([id, descr, source, proteins])
        df = pd.DataFrame(data, columns=["id", "name", "category", "proteins"])
    return df


def read_kegg_data(specifier):
    """
    Reads the KEGG data and returns it as a DataFrame.

    Arguments:
    specifier: the species specifier (e.g. 'mmu' or 'human')
    """
    kegg_df = pd.read_csv(
        f"data/kegg_pathways.{specifier}.tsv",
        delimiter="\t",
        usecols=["id", "name", "genes_external_ids"],
    )
    kegg_df.insert(loc=2, column="category", value="KEGG")
    kegg_df = kegg_df.rename(columns={"genes_external_ids": "proteins"})
    return kegg_df


def data_formatting(species, folder):
    """
    Formats the data to our specifications

    Arguments:
    species: the species which data we want to format
    """
    file_name = os.path.join(folder, f"{species.lower()}_all_pathways.gmt")

    # Read the data from Baderlabs
    df = read_data(file_name)

    # Read the KEGG data
    kegg_df = read_kegg_data(species.lower())

    merged_df = pd.concat([df, kegg_df], ignore_index=True)
    merged_df = merged_df.drop_duplicates(subset=["name", "category"])
    merged_df.to_csv(f"data/AllPathways_{species}.csv")


def download_necessary(filepath):
    """
    Check if new releases are available

    Arguments:
    filepath: filepath of the text file that contains last used release

    Returns:
    Tuple of (bool, bool, string) which correspond to whether KEGG and/or Baderlabs
    respectively have a new release and lastly a string of the versions of both.
    """
    update_kegg = False
    update_geneset = False
    response = requests.get("http://download.baderlab.org/EM_Genesets/")
    kegg_release = f"kegg: {kegg.version()}"
    # get the content of the webpage as a string
    webpage_content = response.text
    geneset_file = f"bader: {util.get_latest_release_date_bader(webpage_content).strftime('%Y-%m-%d')}"
    with open(filepath, "a+") as file:
        file.seek(0)
        content = file.read()
        if len(content) == 0:
            update_geneset = True
            update_kegg = True
        else:
            old_version_geneset = util.search_line(filepath, r"bader: (.*)")
            old_version_kegg = util.search_line(filepath, r"kegg: (.*)")
            if not old_version_geneset or datetime.datetime.strptime(
                old_version_geneset, "%Y-%m-%d"
            ) < util.get_latest_release_date_bader(webpage_content):
                update_geneset = True
            if not old_version_kegg or datetime.datetime.strptime(
                old_version_kegg, "%b %d"
            ) < datetime.datetime.strptime(kegg.version(), "%b %d"):
                update_kegg = True

    return (update_kegg, update_geneset, geneset_file, kegg_release)


def main():
    # Parse CLI arguments
    args = parse_cli_args()
    species_name = args.species_name
    print("Downloading Pathway data for {}.".format(species_name))
    input("Press any key to continue...")
    # Download the data from Baderlabs
    result = download_data(species_name)
    # If input species not supported terminate
    if result != 1:
        print(result)
        return
    print("Download succesfull")
    print("Formatting the data...")
    input("Press any key to continue...")
    data_formatting(species_name)
    print("Formating succesfull")


if __name__ == "__main__":
    main()
