import os
import requests
import zipfile

import shutil
from pymongo import MongoClient

import feedparser
import base64
# import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# 加密函数
def encrypt_text(text, key):
  cipher_suite = Fernet(key)
  encrypted_text = cipher_suite.encrypt(text.encode())
  return encrypted_text


# 解密函数
def decrypt_text(encrypted_text, key):
  cipher_suite = Fernet(key)
  decrypted_text = cipher_suite.decrypt(encrypted_text)
  return decrypted_text.decode()


# 从文件中读取原始文本
def read_text_from_file(filename):
  with open(filename, 'r') as file:
    return file.read()


# 保存文本到文件
def save_text_to_file(text, filename):
  with open(filename, 'w') as file:
    file.write(text)


# 保存密钥到文件
def save_key_to_file(key, filename):
  with open(filename, 'wb') as file:
    file.write(key)


# 从文件中读取密钥
def read_key_from_file(filename):
  with open(filename, 'rb') as file:
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
  # Rest of your code...

  # 使用集合(set)来去除重复行
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
    # 解析RSS订阅
    feed = feedparser.parse(url)

    # 打开文件以写入IP和Port信息
    with open(output_file, "a", encoding="utf-8") as f:
      # 遍历每个RSS项
      for entry in feed.entries:
        # 提取标题中的IP和Port信息
        title = entry.title

        # 排除包含特定文本的项
        if "Subscribe Link" in title:
          continue

        ip_start = title.find("[IP]") + len("[IP]")
        ip_end = title.find("[Port]")
        ip = title[ip_start:ip_end].strip()
        port_start = title.find("[Port]") + len("[Port]")
        port_end = title.find("[Latency]")
        port = title[port_start:port_end].strip()

        # 写入IP和Port到文件中
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
    # 下载文本内容
    response = requests.get(url)
    response.raise_for_status()
    data = response.text

    # 拆分每行数据以逗号作为分隔符
    lines = data.strip().split("\n")

    # 将数据转换为IP PORT格式
    converted_data = []
    for line in lines:
      parts = line.split(",")
      if len(parts) == 3:
        ip, port, _ = parts
        converted_data.append(f"{ip} {port}")

    # 追加转换后的数据到输出文件
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
    # 获取当前目录
    target_directory = "./"

    # 获取源目录中的文件列表
    file_list = os.listdir(source_directory)

    # 移动每个文件到目标目录
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
      print("Failed to download file (HTTP status code:", response.status_code,
            ")")
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
      port = ip_parts[2].split(".")[0]  # Remove .txt extension
      with open(ip_file, "r", encoding="utf-8") as ip_input:
        for line in ip_input:
          line = line.strip()
          if line:  # Skip empty lines
            ip_port = f"{line} {port}"
            if ip_port not in unique_ips:
              unique_ips.add(ip_port)
              ip_output.write(f"{ip_port}\n")
      os.remove(ip_file)  # Delete the original txt file


def save_to_txt(
    file_path,
    database,
    collection,
    filter=None,
    projection={
        "_id": 0,
        "ip": 1,
        "port": 1
    },
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
  # Rest of the code remains the same

  # Connect to MongoDB
  client = MongoClient(os.environ.get("DB_URL"))

  # Retrieve data from MongoDB
  result = client[database][collection].find(filter=filter,
                                             projection=projection)

  # Open the file in write mode
  with open(file_path, "a", encoding="utf-8") as file:
    # Iterate through the result and write ip and port to the file
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
  # Make a GET request to the specified JSON URL
  response = requests.get(json_url)

  # Check if the request was successful (status code 200)
  if response.status_code == 200:
    # Parse the JSON data
    data = response.json()

    # Open the output file in append mode, encoding it with UTF-8
    with open(output_file, "a", encoding="utf-8") as file:
      # Iterate through each key-value pair in the JSON data
      for key, value in data.items():
        # Extract IP and port from the value
        ip = value["ip"]
        port = value["port"]

        # Write the IP and port to the file, separated by a space
        file.write(f"{ip} {port}\n")

    # Print a success message
    print(f"Data appended to {output_file}")
  else:
    # Print an error message if the request was not successful
    print(f"Failed to retrieve data. Status code: {response.status_code}")


if __name__ == "__main__":
  url = "https://zip.baipiao.eu.org"  # 修改为你需要下载的压缩文件的 URL
  url2 = "https://github.com/hello-earth/cloudflare-better-ip/archive/refs/heads/main.zip"
  save_path = os.path.join(os.path.dirname(__file__),
                           "downloaded_file.zip")  # 修改保存路径和文件名
  save_path2 = os.path.join(os.path.dirname(__file__),
                            "downloaded_cfb_file.zip")  # 修改保存路径和文件名
  extract_folder = os.path.dirname(__file__)  # 解压缩文件的目标文件夹为当前脚本所在文件夹

  print("Downloading from:", url)
  if download_file(url, save_path):
    unzip_file(save_path, extract_folder)
    os.remove(save_path)  # 删除下载的压缩文件
  if download_file(url2, save_path2):
    unzip_file(save_path2, extract_folder)
    # 使用示例：将文件从 'cloudflare-better-ip-main/cloudflare/' 目录移动到当前目录
    # move_files_to_current_directory('cloudflare-better-ip-main/cloudflare/')
    # import os

    # 设置源目录和输出文件名
    source_directory = "cloudflare-better-ip-main/cloudflare/"
    output_file = "merged_output.txt"

    # 遍历目录中的所有 .txt 文件并合并它们
    with open(output_file, "w", encoding="utf-8") as merged_file:
      for file_name in os.listdir(source_directory):
        if file_name.endswith(".txt"):
          # Process each .txt file here
          file_path = os.path.join(source_directory, file_name)
          with open(file_path, "r", encoding="utf-8") as txt_file:
            merged_file.write(txt_file.read())

    print("合并完成！输出文件名:", output_file)

    # 有端口 转换为 IP PORT 格式

    # 打开输入文件以及输出文件
    with open(output_file, "r",
              encoding="utf-8") as infile, open("cfbetter-1-443.txt",
                                                "w",
                                                encoding="utf-8") as outfile:
      for line in infile:
        # 拆分每行数据以'|'作为分隔符
        parts = line.strip().split("|")
        if len(parts) >= 2:
          # 获取第一个部分中的IP和端口号
          ip_port = parts[0].strip()
          # 如果端口号在IP后面，使用空格拆分并取第一个元素
          if ":" in ip_port:
            ip, port = ip_port.split(" ")[0].split(":")
            # 写入新的格式到输出文件
            outfile.write(f"{ip}\n")

    print("格式转换完成！输出文件名:", output_file)

    # Remove the file at save_path2
    os.remove(save_path2)

    # Remove the file at output_file
    os.remove(output_file)

    # Remove the directory "cloudflare-better-ip-main" and its contents
    shutil.rmtree("cloudflare-better-ip-main")

    # Call the function to merge IP files
    merge_ip_files()

    # Example of usage: Download and convert data
    cfno1_url = "https://sub.cfno1.eu.org/pure"
    output_file = "merge-ip.txt"
    download_and_convert(cfno1_url, output_file)

    # Specify the RSS subscription URL using an environment variable
    rss_url = os.environ.get("RSS_URL")

    # Extract IP and port information from the specified RSS feed and save to output_file
    extract_ip_port_from_rss(rss_url, output_file)
    # 调用函数
    extract_ip_port_from_fofa(os.environ.get("FOFA_URL"), output_file)
    # Save the extracted data to a text file with specified prefixes and directory
    save_to_txt(output_file, "best_ip", "results")

    # Remove duplicate lines from the output_file
    remove_duplicate_lines(output_file)

    # 原始文本文件
    text_filename = "merge-ip.txt"

    # 密文文件
    # encrypted_text_filename = "encrypted_text.txt"

    # 密钥文件
    key_filename = "key"

    # 从文件中读取原始文本
    text = read_text_from_file(text_filename)

    # 生成随机的盐值
    salt = os.environ.get("SALT_VALUE", "default_salt").encode()

    # 使用PBKDF2-HMAC进行密钥派生
    kdf = PBKDF2HMAC(algorithm=hashes.SHA512(),
                     length=32,
                     salt=salt,
                     iterations=100000)

    # 计算派生密钥
    key = base64.urlsafe_b64encode(kdf.derive(text.encode()))

    # 保存密钥到文件
    save_key_to_file(key, key_filename)

    # 加密文本
    encrypted_text = encrypt_text(text, key)

    # 保存加密后的文本到文件
    save_text_to_file(encrypted_text.decode(), output_file)

    # 从文件中读取密钥
    # key = read_key_from_file(key_filename)

    # 解密文本
    # decrypted_text = decrypt_text(encrypted_text, key)

    # 打印解密的原始文本
    # print(decrypted_text)
