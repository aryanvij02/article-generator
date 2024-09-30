import os
from openai import OpenAI
from dotenv import load_dotenv
from api_request import make_api_request
from image_generator import search_images
import json
import re
import random
from ai_image_generator import generate_image
from upload_to_s3 import upload_to_S3
import time
from google_site_scraper import search
from link_manager import internal_linking_search, external_linking_search
import time

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_article_structure(topic, company_name, product_name, keywords, tone, intent, custom_instructions, company_info, product_info, specific_product_info, section_count, images_per_article, max_retries=3):
    print(f"""
    Topic: {topic}
    Company Name: {company_name}
    Product Name: {product_name}
    Keywords: {keywords}
    Tone: {tone}
    Intent: {intent}
    Custom Instructions: {custom_instructions}
    Company Info: {company_info}
    Product Info: {product_info}
    Specific Product Info: {specific_product_info}
    Section Count: {section_count}
    Images Per Article: {images_per_article}
    """)
    
    print(f"Generating article structure for topic: {topic}")
    prompt = f"""
    Design an article structure for the topic: "{topic}".
    You are writing this article for a specific company for a specific product, here is all the information you are provided.
    
    Company Name: {company_name}
    Company Information: {company_info}
    Product Name: {product_name}
    Product Information: {product_info}
    Keywords: {keywords}
    Tone of the article: {tone}
    Intent: {intent}
    Custom Instructions for the article: {custom_instructions}
    
    You may have to mention specific aspects of the company's products in the article. If Specific Product Info given below is not empty, then you have to make sure that you mention the provided Specific Product Info. This is crucial.
    Specific Product Info: {specific_product_info}
    Once again, remember you have to mention this specific information about the product. Try not to put this information in the section title, but have it in the description so the content contains this info.

    
    In your description, make sure to be very very elaborative. Include exactly which aspects of the product's info, or company info, or specific product info that should be mentioned. This description will be given to a LLM to generate content. 
    This is very important
    
    You must absolutely include one of the three keywords that is provided to you in the TITLE of the article. It cannot be rephrased, try to fit it in EXACTLY.
    But you have to make sure that the content of the article and the title make sense for this keyword. The keyword should be your main focus in devising the article. 
    All other information above is supplementary for you to include in the articles. But PLEASE make sure the title and content makes sense with the keyword.
    Here are the keywords: {keywords}
    
    Make sure to take into account all the information above to formulate your article structure below. 
    Make sure your description is deep and extensive. Include any custom instructions and keywords in the relevant sections.
    
    Your article must not be only focused on the company information or product information. Use that as supplemnetary information that you will include in the article as call to actions.
    However, the topic and content of the article should be focused on the topic given above.
    
    Format the output as JSON with the following structure:
    {{
        "title": "Article Title",
        "summary": [
            "Bullet point 1",
            "Bullet point 2",
            "Bullet point 3"
        ],
        "sections": [
            {{"name": "Section 1 Title", "description": "Brief description of section 1", "include_image": true}},
            {{"name": "Section 2 Title", "description": "Brief description of section 2", "include_image": false}},
            ...
        ]
    }}
    You must have a total of {section_count} sections. 
    Ensure that no more than {int(images_per_article)-1} sections have "include_image" set to true.
    Please do not forget to include the keys specified above, I am begging you. You must have the keys: name, description, include_image
    """
    for attempt in range(max_retries):
        print("Entering this loop")
        try:
            print(f"Attempt {attempt + 1}: Sending request to OpenAI for article structure...")
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional content strategist."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            print("Received article structure from OpenAI")
            content = response.choices[0].message.content
            content = re.sub(r'```(?:json)?\s*', '', content)
            content = content.strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error on attempt {attempt + 1}:")
                print(f"Error message: {str(e)}")
                print("Problematic content:")
                print(content)
                if attempt == max_retries - 1:
                    raise
                else:
                    print("Retrying...")
                    time.sleep(2)  # Wait for 2 seconds before retrying
                    
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                raise
            else:
                print("Retrying...")
                time.sleep(2)  # Wait for 2 seconds before retrying
                
    raise Exception(f"Failed to generate article structure after {max_retries} attempts")
    # print("Sending request to OpenAI for article structure...")
    # response = client.chat.completions.create(
    #     model="gpt-4",
    #     messages=[
    #         {"role": "system", "content": "You are a professional content strategist."},
    #         {"role": "user", "content": prompt}
    #     ]
    # )
    
    # print("Received article structure from OpenAI")
    # content = response.choices[0].message.content
    # content = re.sub(r'```(?:json)?\s*', '', content)
    # content = content.strip()
   
    # return json.loads(content)
    # return json.loads(response.choices[0].message.content)
    
    #######
    # 
from googlesearch import search
import re

def generate_section_content(section_name, section_description, topic, include_image, wordcount_per_section, internal_linking, internal_linking_url, external_linking, keywords):
    print(f"Generating content for section: {section_name}")
    image_instruction = "Include an image suggestion." if include_image else "Do not include any image suggestions."
    externallinking_instruction = '''Include relevant hyperlinks, but instead of providing the actual URL, give a search query that can be used to find a relevant link.
                                    For the text in this hyperlink, make sure it is embedded within the sentence. It shouldn't be a separate word 'source' or 'link', but should be part of a sentence in this section
                                    Use the format: <a href="EXTERNAL_SEARCH:your search query here">link text</a>''' if external_linking else "Do not include any hyperlinks"
    
    internallinking_instruction = '''You must INCLUDE THIS! Include 5 - 10 relevant hyperlinks, but instead of providing the actual URL, give a search query that can be used to find a relevant link.
                                    For the text in this hyperlink, make sure it is embedded within the sentence. It shouldn't be a separate word 'source' or 'link', but should be part of a sentence in this section
                                    Use the format: <a href="INTERNAL_SEARCH:your search query here">link text</a>''' if internal_linking else "Do not include any hyperlinks"                           
 
    prompt = f"""
    Write a {wordcount_per_section} word section for an article about "{topic}".
    Section title: {section_name}
    Section description: {section_description}

    {externallinking_instruction}
    
    {internallinking_instruction}
    
    You must absolutely two of the three keywords that is provided to you in this content. It cannot be rephrased, try to fit in the keyword EXACTLY.
    Here are the keywords: {keywords}
    Select any two that will fit well in the content. 
    
    Use italics for emphasis.
    Bold words that you think should be bolded, like keywords, emphasized words, etc.
    Add necessary line breaks <br/> where necessary, to separate different sections.
    Format the content in HTML, using appropriate tags (<p>, <em>, etc.).
    Use proper paragraph spacing and line breaks where necessary for readability.
    Never ever return ```html before the actual html. Just give the pure html please

    {image_instruction}
    If suggesting an image, use the format: <img-suggestion>Description of the image</img-suggestion>
    Ensure there's always a paragraph of text before and after an image suggestion.
    
    Never return ```json before the actual JSON. Only return the actual JSON. 
    
    Really genuinely make sure to never EVER return ```json before the actual JSON. Only return the actual JSON. 
    """
    
    print("Sending request to OpenAI for section content...")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional content writer."},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content
    print("Received section content from OpenAI")
    
    # Parse the content and replace search queries with actual URLs
    def add_delay(func):
        def wrapper(*args, **kwargs):
            time.sleep(10)  # Add a 1-second delay
            return func(*args, **kwargs)
        return wrapper

    @add_delay
    def rate_limited_internal_linking_search(internal_linking_url, query):
        return internal_linking_search(internal_linking_url, query)
    
    def escape_regex(text):
        return re.escape(text)
    
    content = re.sub(r'href="EXTERNAL_SEARCH:(.*?)"', lambda m: external_linking_search(escape_regex(m.group(1))), content)
    content = re.sub(r'href="INTERNAL_SEARCH:(.*?)"', lambda m: rate_limited_internal_linking_search(internal_linking_url, escape_regex(m.group(1))), content)

    return content

def add_line_spacing(content):
    # Add line-height to paragraphs and list items
    content = re.sub(r'<p>', '<p style="line-height: 1.6;">', content)
    content = re.sub(r'<li>', '<li style="line-height: 1.6;">', content)
    
    # Add margin to headings
    content = re.sub(r'<h4>', '<h4 style="margin-top: 1.2em; margin-bottom: 0.5em;">', content)
    
    return content

def downgrade_headings(content):
    # Replace h1, h2, h3 with h4
    content = re.sub(r'<h[123]', '<h4', content) #Set to h2 now!
    content = re.sub(r'</h[123]>', '</h4>', content)
    return content


def business_info_extraction(topic, company_info, product_info):
    prompt = f"""
    You are a business information extractor. You are given information about a company and their product.
    For a given topic, you need to extract only the relevant information that could be useful to generate an article about this topic.
    This information should be easily integrated into the article. 
    
    Topic: {topic}
    Company Information: {company_info}
    Product Information: {product_info}
    """
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a business information extractor."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

def generate_blog_topic(keywords, tone, intent, company_info, product_info, custom_instructions, previous_topics):
    prompt = f"""
    Your job is to generate a good topic to write a article or blog on
    I will provide you with important keywords that we want to hit, the intent of the article, the tone, the company this article if for, the product this article is for, and any custom instructions. Make sure it is a good descriptive one liner topic
    keywords: {keywords}
    tone: {tone}
    intent: {intent}
    company information: {company_info}
    product information: {product_info}
    custom_instructions: {custom_instructions}
    
    Make sure that you do not create a topic that is the same as any of these: {previous_topics}. This is EXTREMELY IMPORTANT!
    Your topic also does not have to be ABOUT the company or the product specifically, it can revolve around a surrounding topic or concept.
    """
    
    print("Sending request to OpenAI for generating topic...")
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a professional content writer."},
            {"role": "user", "content": prompt}
        ]
    )
    
    print("Received topic from OpenAI")
    return response.choices[0].message.content
    

def generate_blog_post(topic, company_name, product_name, company_info, product_info, mention_product, 
                                            specific_product_info, keywords, tone, intent, custom_instructions, internal_linking, internal_linking_url, external_linking, section_count, wordcount_per_section, images_per_article):
    print(f"Starting blog post generation for topic: {topic}")
    
    #Article Structure Generation
    if mention_product:
        print("This is mentioned product")
        concised_information = business_info_extraction(topic, company_info, product_info)
        #I have commented out the product info below
        article_structure = generate_article_structure(topic, company_name, product_name, keywords, tone, intent, custom_instructions, "", concised_information, specific_product_info, section_count, images_per_article)
    else:
        concised_information = business_info_extraction(topic, company_info, product_info)
        article_structure = generate_article_structure(topic, company_name, product_name, keywords, tone, intent, custom_instructions, "", concised_information, "", section_count, images_per_article) #Not passing in specific product information

    
    print("Article structure generated. Generating content for each section...")
    
    
    # Summary Section generation
    full_content = "<h4>Summary</h4><ul>"
    for bullet in article_structure['summary']:
        full_content += f"<li>{bullet}</li>"
    full_content += "</ul>"
    
    
    #Creating each individual section
    image_count = 0
    print("Starting section creation")
    for section in article_structure['sections']:
        print("This is section number: {section}")
        section_content = generate_section_content(section['name'], section['description'], topic, section['include_image'] and image_count < images_per_article-1, wordcount_per_section, internal_linking, internal_linking_url, external_linking, keywords)
        full_content += f"<h4>{section['name']}</h4>{section_content}"
        
        if section['include_image'] and image_count < images_per_article-1:
            img_suggestions = re.findall(r'<img-suggestion>(.*?)</img-suggestion>', section_content)
            if img_suggestions:
                suggestion = img_suggestions[0].strip()
                if suggestion:
                    print(f"Searching for image: {suggestion}")
                    dalle_2_image_url = generate_image(suggestion)
                    image_url, success = upload_to_S3(dalle_2_image_url)
                    if success:
                        img_tag = f'<p><img src="{image_url}" alt="{suggestion}" style="border-radius: 5px; margin-top: 1em; margin-bottom: 1em;"></p>'
                        full_content = full_content.replace(f'<img-suggestion>{suggestion}</img-suggestion>', img_tag, 1)
                        image_count += 1
                    else:
                        print(f"Failed to upload image for suggestion: {suggestion}")
                        full_content = full_content.replace(f'<img-suggestion>{suggestion}</img-suggestion>', '', 1)
                else:
                    print("Empty image suggestion found, removing tag")
                    full_content = full_content.replace('<img-suggestion></img-suggestion>', '', 1)
            
            # Remove any additional image suggestions in this section
            full_content = re.sub(r'<img-suggestion>.*?</img-suggestion>', '', full_content)
    
    full_content = downgrade_headings(full_content)
    full_content = add_line_spacing(full_content)
    
    print("Blog post generation complete")
    return article_structure['title'], full_content


# Remove the main function from here
# if __name__ == "__main__":
    # test = generate_section_content("Generating SEO articles", "How SEO has helped companies grow", "topHow SEO has helped companies growic", False)
    # print(test)
    # topic = "The Impact of AI on Digital Marketing"
    # company_name = "TechInnovate Solutions"
    # product_name = "AI Marketing Assistant"
    # keywords = ["AI", "digital marketing", "automation", "ROI"]
    # tone = "professional and informative"
    # intent = "educate and promote"
    # custom_instructions = "Include case studies of successful AI implementations in marketing."
    # company_info = "TechInnovate Solutions is a leading AI software company."
    # product_info = "AI Marketing Assistant helps businesses optimize their digital marketing strategies."
    # specific_product_info = "Our AI Marketing Assistant can increase conversion rates by 30%."
    # section_count = 5
    # images_per_article = 3

    # article_structure = generate_article_structure(
    #     topic, company_name, product_name, keywords, tone, intent, 
    #     custom_instructions, company_info, product_info, specific_product_info, 
    #     section_count, images_per_article
    # )

    # print(json.dumps(article_structure, indent=2))
