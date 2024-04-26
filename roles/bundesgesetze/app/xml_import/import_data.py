from bs4 import BeautifulSoup
from collections import namedtuple
from io import BytesIO
from urllib.parse import urljoin, urlencode, urlparse, urlunparse, urlunsplit, urlsplit
from zipfile import ZipFile
import logging
import os
import psycopg2
import re
import requests
import urllib.request


logger = logging.getLogger(__name__)
logging.basicConfig(filename='bundesgesetze.log', level=logging.INFO)


class Bundesgesetze:
  def __init__(self):
    self.origin = "https://www.gesetze-im-internet.de"
    self.toc_path = "/gii-toc.xml"
    self.books: list[LawBook] = []
    self.get_book_links()

  def get_book_links(self):
    url = urljoin(self.origin, self.toc_path)

    if (url):
      logger.info(f'fetch books from {url}')
    else:
      logger.error(f'no valid url with origin {self.origin} and path {self.toc_path}')
      
    response = requests.get(url=url)

    if (response.status_code != 200):
      logger.error(f'couldn t get answer from {url}')
      exit()
    #else:
    # logger.info(f'got {response.text}')

    soup = BeautifulSoup(response.text, features="xml")
    items = soup.find_all("item")

    index = 0
    for item in items:
      if (index > 2):
        break
      else:
        index += 1
      
      print(f'get_book_links: found item {item}')

      xml_zip_url = item.find("link")
      title = item.find("title")
      logger.info(f'found link for zip url {xml_zip_url.text} for title {title.text}')
      
      if (str(xml_zip_url) and str(title)):
        self.books.append(LawBook(xml_zip_url.text, title.text))


class LawBook:
  def __init__(self, xml_zip_url="", title=""):
    self.xml_folder = "./Downloads"
    self.book_table_name = "bundesgesetze.books"

    self.selectors = {
        "amtabk":  "norm metadaten amtabk",
        "jurabk": "norm metadaten jurabk",
        "description": "norm metadaten langue",
        "updated_at": "norm metadaten ausfertigung-datum"
    }

    self.xml_zip_url = xml_zip_url

    self.xml_file_name = self.create_xml_filename_from_url(self.xml_zip_url)
    self.xml_text = self.fetch_xml_content_from_xml_zip_url(self.xml_zip_url)
    self.write_content_to_file(self.xml_text, self.xml_file_name)
    self.xml_tree = self.parse_xml_content(self.xml_text)
    self.book_info = self.get_book_info(self.xml_tree)
    self.book_info["id"] = self.db_insert_book_info(self.book_info)
    
    self.paragraphs = LawParagraph(self.xml_tree, self.book_info)


  def __str__(self):
    return f'{self.book_info.amtabk} - {self.book_info.jurabk}'


  def create_xml_filename_from_url(self, url: str):
    splittedUrl = urlsplit(url)
    filename = f'{splittedUrl.path.replace("/xml.zip", "").replace("/", "")}.xml'
    logger.info(f'filename {filename}\n')
    return filename


  def fetch_xml_content_from_xml_zip_url(self, url):
    logger.info(f'fetch_xml_content_from_xml_zip_url from {url}\n')
    response = requests.get(url)
    result = ""

    if (response.status_code != 200):
      logger.error(f'invalid response: {response}')
      return result
    
    with ZipFile(BytesIO(response.content)) as zip_file:
      unzipped_file = zip_file.open(name = zip_file.namelist()[0], mode = 'r')
      result = str(unzipped_file.read(), "UTF-8")
      unzipped_file.close()
      
    #logger.info(f'got xml_content {result}')
    return result
    
  
  def write_content_to_file(self, content, filename, folder = "./Downloads"):
    if (filename):
      with open(f'{folder}/{filename}', "w+") as file:
        file.write(content)
        
        
  def parse_xml_content(self, xml_content):
    logger.info(f'parse xml')
    parsed_xml = BeautifulSoup(markup = xml_content, features = "xml")
    return parsed_xml


  def get_book_info(self, xml_tree):
    amtabk = xml_tree.select_one(self.selectors["amtabk"])
    description = xml_tree.select_one(self.selectors["description"])
    jurabk = xml_tree.select_one(self.selectors["jurabk"])
    updated_at = xml_tree.select_one(self.selectors["updated_at"])

    if amtabk is None:
      amtabk = jurabk

    logger.info(f'get_book_info found amtabk {amtabk.text} and jurabk {jurabk.text}')
    
    amtabk = f'{amtabk.text}'.replace("/", "_")
    description = f'{description.text}'
    jurabk = f'{jurabk.text}'.replace("/", "_")
    updated_at = f'{updated_at.text}'


    book_info = {
      "id": None,
      "amtabk": amtabk, 
      "description": description, 
      "jurabk": jurabk, 
      "updated_at": updated_at
    }
    
    logger.info(
        f'get_book_info: {book_info} jurabk: {book_info["jurabk"]}, amtabk: {book_info["amtabk"]}, description: {book_info["description"]}, updated_at: {book_info["updated_at"]}\n')
    
    return book_info

  
  def db_insert_book_info(self, law_book):
    logger.info(f'db_insert_book_info {law_book} jurabk {law_book["jurabk"]}')
    sql_check_book_exists = "SELECT id FROM bundesgesetze.books WHERE jurabk = %s AND updated_at = %s;"
    sql_insert_book_info = "INSERT INTO bundesgesetze.books(amtabk, jurabk, description, updated_at) VALUES(%s, %s, %s, %s) RETURNING id;"
    rows = []
    book_id = None

    try:
      with psycopg2.connect("dbname=postgres host=localhost user=postgres password=password port=5555") as connection:
        with connection.cursor() as cur:
          ####################################
          # check if book already exists
          ####################################
          cur.execute(sql_check_book_exists, (law_book["jurabk"], law_book["updated_at"], ))
          book_exists = cur.fetchone()
          logger.info(f'found book {book_exists}')
          ####################################
          # INSER book if not already exists
          ####################################
          if (len(book_exists) == 0):
            cur.execute(sql_insert_book_info, (law_book["amtabk"], law_book["jurabk"], law_book["description"], law_book["updated_at"], ))
            rows = cur.fetchone()
            if rows:
              book_id = rows[0]
          else:
            book_id = book_exists[0]
          ####################################
          # INSER book list
          ####################################
          # execute the INSERT statement
          # cur.executemany(sql, book_list)

          # obtain the inserted rows
          # rows = cur.fetchall()

          # commit the changes to the database
          connection.commit()
          return book_id
    except (Exception, psycopg2.DatabaseError) as error:
      print(error)
    finally:
      return book_id


  """ def genreate_books_download_from_parts_list(self, path="/Teilliste_A.html"):
    url = urlunparse(
        Components(
            scheme='https',
            netloc=self.bundesgesetze_origin,
            query=None,  # urlencode(query_params),
            url=path,
            path="",
            fragment="",
        )
    )
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html, features="html.parser")
    container = soup.find("div", id="container")
    books = []

    for link in container.find_all("a"):
      if (link['href'].endswith(".html")):
        books.append({
            "xml_path": link['href'][1:].replace("index.html", "xml.zip"),
            "title": link.abbr["title"],
            "jurabk": link.abbr.contents[0].rstrip().replace("/", "_")
        })

    # print(f'generated books  {books}')
    return books
 """


class LawParagraph:
  def __init__(self, xml_tree, book_info):
    self.book = book_info
    self.db_book_table_name = "bundesgesetze.books"
    self.xml_tree = xml_tree
    self.selectors = {
        "section": "gliederungseinheit gliederungsbez",
        "section_title": "gliederungseinheit gliederungstitel",
        "enbez": "metadaten enbez",
        "parapgraphs": "textdaten text Content P"
    }

    self.content =  self.get_book_paragraphs(self.xml_tree)
  
  def db_get_book_info(self, book_id):
    sql_select_book = f'SELECT * from {self.db_book_table_name} WHERE id = {book_id};'
    book: TLawBook = None
    try:
      with psycopg2.connect("dbname=postgres host=localhost user=postgres password=password port=5555") as connection:
        with connection.cursor() as cur:
          ####################################
          # SELECT one book
          ####################################
          cur.execute(sql_select_book, (book_id, ))
          rows = cur.fetchone()
          if rows:
            book = rows[0]
    except (Exception, psycopg2.DatabaseError) as error:
      logger.info(f'ERROR db_get_book_info: {error}')
    finally:
      return book
  
  
  def get_book_paragraphs(self, xml_tree):
    logger.info(f'type of paragraph tree is {type(xml_tree)}')
    paragraphs = []
    if (xml_tree == None):
      return
    
    index = 0
    lawParagraph = None
    
    for norm in xml_tree.find_all("norm"):
      #logger.info(f'search in norm {norm}')
      # jump over first norm, because this norm only contains only information about the book itself
      if (index < 1):
        index += 1
        continue

      section_xml = norm.select_one(self.selectors["section"])
      section_text = ""
      section_title_xml = norm.select_one(self.selectors["section_title"])
      section_title_text = ""
      enbez_xml = norm.select_one(self.selectors["enbez"])
      enbez_text = ""
      parapgraphs_xml = norm.select(self.selectors["parapgraphs"])

      if (section_xml):
        logger.info(f'section {section_xml.text}'.replace("\n", ""))
        section_text = section_xml.text

      if (section_title_xml):
        logger.info(
            f'section_title {section_title_xml.text}'.replace("\n", ""))
        section_title_text = section_title_xml.text

      if (enbez_xml):
        # with content {content.text}')
        logger.info(f'enbez {enbez_xml.text}\n')
        enbez_text = enbez_xml.text
      else:
        logger.info(f'no enbez in {self.book["jurabk"]} got {norm}\n')

      markdown_result = ""
      
      if (parapgraphs_xml and len(parapgraphs_xml) > 0):
        for p in parapgraphs_xml:
          print(f' found p {p} ')
          markdown_list = ""
          markdown_result += f'- {p.text}'

          if (p.select("DL")):
            markdown_list = self.transform_list(p)
            list_items = markdown_list.split("\n")
            
            for item in list_items:
              numeration = re.findall("^\d+\. ", item)
              markdown_result = markdown_result.replace(
                  re.sub("^  (\d+\.) ", '\\1', item), "")

          markdown_result += f'\n{markdown_list}'
          
          lawParagraph = {
            "book_id": self.book["id"],
            "enbez": enbez_text,
            "section": section_text,
            "section_title": section_title_text,
            "markdown": markdown_result,
          }
          paragraphs.append(lawParagraph)
          logger.info(f'lawParagraph \n{lawParagraph}')
      else:
        logger.info(f'no content in {self.book["amtabk"]}')

    return paragraphs
    
    
  def transform_list(self, paragraph):
    mardown_list = ""

    all_lists = paragraph.select("DL")

    if (all_lists):
      for _list in all_lists:
        for element in _list.find_all(["DT", "DD"]):

          if (element.name == "DT"):
            # this 2 spaces at the beginning are important to indent the list items accordingly in markdown. The appended space is also important
            mardown_list += f'  {element.text} '

          if (element.name == "DD"):
            content = element.find("LA")
            if (content):
              mardown_list += f'{content.text}\n'
            else:
              mardown_list += "-"

    #print(f'mardown_list \n{mardown_list}')
    return mardown_list
  
  
  def insert_paragraphs(self, paragraph):
    """ Insert multiple law paragraphs into the parapgraphs table  """

    sql = "INSERT INTO bundesgesetze.paragraphs(book_id, section, section_title, enbez, markdown) VALUES(%d, %s, %s, %s, %s) RETURNING book_id;"
    rows = []
    book_id = None

    try:
      with psycopg2.connect("dbname=postgres host=localhost user=postgres password=password port=5555") as conn:
        with conn.cursor() as cur:
          ####################################
          # INSER one paragraph
          ####################################
          cur.execute(sql, (paragraph["book_id"], paragraph["section"], paragraph["section_title"], paragraph["enbez"], paragraph["markdown"], ))

          # get the paragraph id back
          rows = cur.fetchone()
          if rows:
            book_id = rows[0]
          ####################################
          # INSER book list
          ####################################
          # execute the INSERT statement
          # cur.executemany(sql, book_list)

          # obtain the inserted rows
          # rows = cur.fetchall()

          # commit the changes to the database
          conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
      print(error)
    finally:
      return book_id


if __name__ == '__main__':
  laws = Bundesgesetze()

  # books_downloads = laws.genreate_books_download_from_parts_list()
  #
  # index = 0
  #
  # for book in books_downloads:
  #  if (index > 1):
  #    break
  #
  #  index += 1
  #  #print(_book["xml_path"])
  #  laws.load_xml(book["xml_path"])
  #  print(laws.get_book_info())
  #  print(laws.get_book_paragraphs())
  #  laws.write_xml_file_to_disk()
  # with open(os.path.join('./downloads/', _book["jurabk"] + ".xml"), "w") as reader:
  #  reader.write(_book["xml_path"])

  # print(f'download {download} ')
  # book.load_xml(book.bundesgesetze_origin + download["xml"])
  # print(get_book_info())
  # Iterate over each element in the XML file
  """ for norm in dokumente:
    print(norm.tag)
    book = norm.find("./metadaten/jurabk")
    print(book.text)
    paragraph = norm.find("./metadaten/enbez")
    if (getattr(paragraph, "text", None)):
      print(paragraph.text) """

  """ print(norm.iter("jurabk"))
  # Handle nested elements
  for child in norm:
      child_data = child.text
        #print("child " + child) """