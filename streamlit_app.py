import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import pandas as pd
import streamlit as st


def get_main_prod_data(product):
    base_url = "https://www.flipkart.com"

    flipkart_url = f"{base_url}/search?q={product}"
    uClient = urlopen(flipkart_url)
    flipkart_page = uClient.read()
    uClient.close()
    return flipkart_page, base_url


def get_first_product_link(flipkart_page, base_url):
    flipkart_html = bs(flipkart_page, "html.parser")
    bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
    del bigboxes[0:3]
    box = bigboxes[0]
    product_link = base_url + box.div.div.div.a["href"]
    return product_link


def get_prod_page_data(product_link):
    prodRes = requests.get(product_link)
    prodRes.encoding = "utf-8"
    prod_html = bs(prodRes.text, "html.parser")
    return prod_html


def get_all_review_link(prod_html, base_url):
    all_comment = [
        prd.get("href")
        for prd in prod_html.find_all("a")
        if prd.get("href").split("&")[-1] == "marketplace=FLIPKART"
    ][0]
    all_comment_link = base_url + all_comment
    return all_comment_link


def get_each_review_box(final_link):
    comment_page_res = requests.get(final_link)
    comment_page_res.encoding = "utf-8"
    comment_page_html = bs(comment_page_res.text, "html.parser")
    review_boxes = comment_page_html.find_all("div", {"class": "_1AtVbE col-12-12"})
    return review_boxes


@st.cache_data()
def scrape_flipkart_review_data(product):
    flipkart_page, base_url = get_main_prod_data(product)

    product_link = get_first_product_link(flipkart_page, base_url)

    prod_html = get_prod_page_data(product_link)

    # total_data = prod_html.find_all("div", class_="_3UAT2v _16PBlm")
    # len_comment_box = int(total_data[0].text.split(" ")[1]) / 10

    all_comment_link = get_all_review_link(prod_html, base_url)

    reviews = []

    for page_no in range(1, 11):
        try:
            final_link = f"{all_comment_link}&page={page_no}"

            review_boxes = get_each_review_box(final_link)

            for comment_box in review_boxes:

                try:
                    name = comment_box.div.div.find_all(
                        "p", {"class": "_2sc7ZR _2V5EHH"}
                    )[0].text

                except:
                    name = ""

                try:
                    rating = comment_box.div.div.div.div.text[0]

                except:
                    rating = "No Rating"

                try:
                    comment_head = comment_box.div.div.div.p.text

                except:
                    comment_head = "No Comment Heading"

                try:
                    comtag = comment_box.div.div.find_all("div", {"class": ""})
                    cust_comment = comtag[0].div.text

                except Exception as e:
                    pass

                if name != "":
                    review_dict = {
                        "Name": name,
                        "Rating": rating,
                        "Comment_head": comment_head,
                        "Comment": cust_comment,
                        "Link": final_link,
                    }

                    reviews.append(review_dict)
        except:
            pass

    df = pd.DataFrame(reviews)
    return df, product_link


st.header("Flipkart Review Scrapper")
product = st.text_input("Enter product name : ")


if product:
    searchString = product.replace(" ", "")

    df, product_link = scrape_flipkart_review_data(searchString)

    st.subheader(product)
    st.dataframe(df)
    csv_data = df.to_csv(index=False)

    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f'{product.replace(" ", "_")}.csv',
        mime="text/csv",
    )
