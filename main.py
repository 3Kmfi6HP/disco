import os
import requests
import zipfile

import shutil
from pymongo import MongoClient

import feedparser
import base64


from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def encrypt_text(text, key):
    cipher_suite = Fernet(key)
    encrypted_text = cipher_suite.encrypt(text.encode())
    return encrypted_text


def decrypt_text(encrypted_text, key):
    cipher_suite = Fernet(key)
    decrypted_text = cipher_suite.decrypt(encrypted_text)
    return decrypted_text.decode()


def read_text_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


def save_text_to_file(text, filename):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)


def save_key_to_file(key, filename):
    with open(filename, "wb") as file:
        file.write(key)


def read_key_from_file(filename):
    with open(filename, "rb") as file:
        return file.read()


def remove_duplicate_lines(file_path):
    """
    Remove duplicate lines from a file.

    Parameters:
    - file_path (str): The path to the file.

    Returns:
    - None
    """
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    unique_lines = set(lines)

    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(unique_lines)


def extract_ip_port_from_rss(url, output_file):
    """
    Extracts IP and port information from an RSS feed.

    Args:
        url (str): The URL of the RSS feed.
        output_file (str): The file to which the extracted information will be written.

    Returns:
        None
    """
    try:
        feed = feedparser.parse(url)

        with open(output_file, "a", encoding="utf-8") as f:
            for entry in feed.entries:
                title = entry.title

                if "Subscribe Link" in title:
                    continue

                ip_start = title.find("[IP]") + len("[IP]")
                ip_end = title.find("[Port]")
                ip = title[ip_start:ip_end].strip()
                port_start = title.find("[Port]") + len("[Port]")
                port_end = title.find("[Latency]")
                port = title[port_start:port_end].strip()

                f.write(f"{ip} {port}\n")

        print(f"提取完成，并已写入文件：{output_file}")
    except Exception as e:
        print(f"发生错误：{str(e)}")


def download_and_convert(url, output_file):
    """
    Downloads content from the given URL and saves it to the specified output file.

    Parameters:
    - url (str): The URL from which to download the content.
    - output_file (str): The file path where the downloaded content will be saved.

    Returns:
    None
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.text

        lines = data.strip().split("\n")

        converted_data = []
        for line in lines:
            parts = line.split(",")
            if len(parts) == 3:
                ip, port, _ = parts
                converted_data.append(f"{ip} {port}")

        with open(output_file, "a") as outfile:
            outfile.write("\n".join(converted_data) + "\n")

        print("数据已转换并追加到文件:", output_file)
    except Exception as e:
        print(f"发生错误：{e}")


def move_files_to_current_directory(source_directory):
    """
    Move files from the specified source directory to the current working directory.

    Parameters:
    - source_directory (str): The path to the source directory containing the files to be moved.

    Returns:
    None
    """
    try:
        target_directory = "./"

        file_list = os.listdir(source_directory)

        for file_name in file_list:
            source_path = os.path.join(source_directory, file_name)
            target_path = os.path.join(target_directory, file_name)
            shutil.move(source_path, target_path)

        print("文件已移动到当前目录")
    except Exception as e:
        print(f"发生错误：{e}")


def download_file(url, save_path):
    """
    Download a file from the given URL and save it to the specified path.

    Parameters:
    - url (str): The URL of the file to be downloaded.
    - save_path (str): The path where the downloaded file will be saved.

    Returns:
    - None
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = url.split("/")[-1]
            with open(save_path, "wb") as file:
                file.write(response.content)
            print(f"Downloaded {filename} and saved as {save_path}")
            return True
        else:
            print(
                "Failed to download file (HTTP status code:", response.status_code, ")"
            )
    except Exception as e:
        print("An error occurred:", e)
    return False


def unzip_file(zip_path, extract_folder):
    """
    Unzips a specified zip file to the specified extraction folder.

    Parameters:
    - zip_path (str): The path to the zip file to be extracted.
    - extract_folder (str): The folder where the contents of the zip file will be extracted.

    Returns:
    None
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_folder)
        print("Extracted files to:", extract_folder)


def merge_ip_files():
    """
    Merge multiple IP files.

    This function reads a list of IP files in the current directory and merges them.

    Parameters:
    None

    Returns:
    None
    """
    ip_files = []
    for file_name in os.listdir():
        if file_name.endswith(".txt") and len(file_name.split("-")) == 3:
            ip_files.append(file_name)

    unique_ips = set()
    with open("merge-ip.txt", "w", encoding="utf-8") as ip_output:
        for ip_file in ip_files:
            ip_parts = ip_file.split("-")
            ip = ip_parts[0]
            port = ip_parts[2].split(".")[0]
            with open(ip_file, "r", encoding="utf-8") as ip_input:
                for line in ip_input:
                    line = line.strip()
                    if line:
                        ip_port = f"{line} {port}"
                        if ip_port not in unique_ips:
                            unique_ips.add(ip_port)
                            ip_output.write(f"{ip_port}\n")
            os.remove(ip_file)


def save_to_txt(
    file_path,
    database,
    collection,
    filter=None,
    projection={"_id": 0, "ip": 1, "port": 1},
):
    """
    Save data from a MongoDB collection to a text file.

    Parameters:
    - file_path (str): The path to the text file where data will be saved.
    - database (str): The name of the MongoDB database.
    - collection (str): The name of the MongoDB collection.
    - custom_filter (dict, optional): A custom filter for querying data.
    - projection (dict, optional): A projection for selecting specific fields (default is None).

    Returns:
    None
    """

    client = MongoClient(os.environ.get("DB_URL"))

    result = client[database][collection].find(filter=filter, projection=projection)

    with open(file_path, "a", encoding="utf-8") as file:
        for entry in result:
            file.write(f"{entry['ip']} {entry['port']}\n")

    print(f"Data has been saved to {file_path}")


import requests


def extract_ip_port_from_fofa(json_url, output_file):
    """
    Extracts IP addresses and ports from a JSON file obtained from a given URL
    and appends them to the specified output file.

    Parameters:
        json_url (str): The URL of the JSON file containing IP and port data.
        output_file (str): The path to the output file where data will be appended.

    Returns:
        None
    """

    response = requests.get(json_url)

    if response.status_code == 200:
        data = response.json()

        with open(output_file, "a", encoding="utf-8") as file:
            for key, value in data.items():
                ip = value["ip"]
                port = value["port"]

                file.write(f"{ip} {port}\n")

        print(f"Data appended to {output_file}")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


if __name__ == "__main__":
    url = "https://zip.baipiao.eu.org"
    url2 = "https://github.com/hello-earth/cloudflare-better-ip/archive/refs/heads/main.zip"
    save_path = os.path.join(os.path.dirname(__file__), "downloaded_file.zip")
    save_path2 = os.path.join(os.path.dirname(__file__), "downloaded_cfb_file.zip")
    extract_folder = os.path.dirname(__file__)

    if download_file(url, save_path):
        unzip_file(save_path, extract_folder)
        os.remove(save_path)
    if download_file(url2, save_path2):
        unzip_file(save_path2, extract_folder)

        source_directory = "cloudflare-better-ip-main/cloudflare/"
        output_file = "merged_output.txt"

        with open(output_file, "w", encoding="utf-8") as merged_file:
            for file_name in os.listdir(source_directory):
                if file_name.endswith(".txt"):
                    file_path = os.path.join(source_directory, file_name)
                    with open(file_path, "r", encoding="utf-8") as txt_file:
                        merged_file.write(txt_file.read())

        print("合并完成！输出文件名:", output_file)

        with open(output_file, "r", encoding="utf-8") as infile, open(
            "cfbetter-1-443.txt", "w", encoding="utf-8"
        ) as outfile:
            for line in infile:
                parts = line.strip().split("|")
                if len(parts) >= 2:
                    ip_port = parts[0].strip()

                    if ":" in ip_port:
                        ip, port = ip_port.split(" ")[0].split(":")

                        outfile.write(f"{ip}\n")

        print("格式转换完成！输出文件名:", output_file)

        os.remove(save_path2)

        os.remove(output_file)

        shutil.rmtree("cloudflare-better-ip-main")

        merge_ip_files()

        cfno1_url = "https://sub.cfno1.eu.org/pure"
        output_file = "merge-ip.txt"
        download_and_convert(cfno1_url, output_file)

        rss_url = os.environ.get("RSS_URL")

        extract_ip_port_from_rss(rss_url, output_file)

        # extract_ip_port_from_fofa(os.environ.get("FOFA_URL"), output_file)

        # save_to_txt(output_file, "best_ip", "results")

        remove_duplicate_lines(output_file)

        text_filename = "merge-ip.txt"

        encrypted_text_filename = "encrypted.txt"

        key_filename = "key"

        text = read_text_from_file(text_filename)

        salt = os.environ.get("SALT_VALUE", "default_salt").encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(), length=32, salt=salt, iterations=100000
        )

        key = base64.urlsafe_b64encode(kdf.derive(text.encode()))

        save_key_to_file(key, key_filename)

        encrypted_text = encrypt_text(text, key)

        save_text_to_file(encrypted_text.decode(), encrypted_text_filename)
