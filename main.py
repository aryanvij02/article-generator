import os
from dotenv import load_dotenv
from api_request import make_api_request
from blog_generator import generate_blog_post
from blog_generator import generate_blog_topic
from image_generator import search_images
from openai import OpenAI
import re
import unicodedata
from blog_content import blog_post_titles
from ai_image_generator import generate_image
import json
from datetime import datetime
from company_data import aifd_data, am_data

load_dotenv()

WEBFLOW_API_TOKEN = None
# os.getenv("WEBFLOW_API_KEY")
COLLECTION_ID = None
# os.getenv("WEBFLOW_COLLECTION_ID")
SITE_ID = None
# os.getenv("WEBFLOW_SITE_I D")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_summary(title, content):
    prompt = f"Summarize the following article in 2-3 sentences:\n\nTitle: {title}\n\nContent: {content}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional content summarizer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def generate_hashtags(title, content):
    prompt = f"Generate 4-5 relevant hashtags for the following article:\n\nTitle: {title}\n\nContent: {content}. Just seperate each hashtag with spaces, don't add numbers. YOU SHOULD NOT HAVE 1. 2. 3. etc"
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a social media expert."},
            {"role": "user", "content": prompt}
        ]
    )
    hashtags = response.choices[0].message.content.strip().split()
    return " ".join(hashtags[:5])  # Ensure we only return up to 5 hashtags

def generate_keywords(keyword_theme):
    prompt = f'''
    You are given a theme to generate Google Search Keywords that will trend. Based on this theme, I want you to generate 
    10 relevant keywords that will rank on Google. 
    
    Keyword Theme: {keyword_theme}
    
    You are to return a list of keywords, for example: "phone receptionists, automate calls, etc, etc"
    '''
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a social media expert."},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content.strip()
    return content 

def generate_slug(keyword, topic):
    prompt = f'''
    You are given a keyword for ranking on Google.
    If the keyword is already 3 to 5 words long, return it.
    Else, change it to something that is 3 to 5 words long, by just adding words before and after it.
    For example if the keyword is "phone" then you can make it "ai phone receptionists"
    Always just return pure string, nothing else.
    You are also given the topic of the article so you have some context
    
    Keyword: {keyword}
    Topic of Article: {topic}
    '''
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a social media expert."},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content.strip()
    return content 
    
    
def create_blog_post(title, content, slug_input):
    print(f"Creating blog post with title: {title}")
    url = f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/items"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {WEBFLOW_API_TOKEN}"
    }
    
    # Create a more robust slug
    def slugify(text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        text = text.strip('-')
        text = re.sub(r'-+', '-', text)
        return text
    
    slug = slugify(slug_input)  
    
    # Generate summary
    summary = generate_summary(title, content)
    
    # Generate hashtags
    hashtags = generate_hashtags(title, content)
    
    # Get main image
    # main_image_keyword = title.split()[0]  # Use the first word of the title as the keyword
    # image_urls = search_images(main_image_keyword, num_images=1)
    main_image_url = generate_image(title)
    # main_image_url = image_urls[0] if image_urls else ""
    
    data = {
        "fieldData": {
            "name": title,
            "slug": slug,
            "post-body": content,
            "post-summary": summary,
            "main-image": main_image_url,
            "thumbnail-image": main_image_url,
            "hashtags": hashtags
        }
    }
    print(f"Data being sent: {data}")
    print("Sending request to Webflow API...")
    response = make_api_request(url, method='POST', headers=headers, json=data)
    print("Received response from Webflow API")
    return response

def save_blog_post_info(title):
    file_path = "../dashboard/dashboard/public/published.json"
    
    # Create the blog post info
    blog_post_info = {
        "name": title,
        "time": datetime.now().isoformat()
    }
    
    try:
        # Read existing data
        with open(file_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty/invalid, start with an empty list
        data = []
    
    # Append new blog post info
    data.append(blog_post_info)
    
    # Write updated data back to file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Blog post info saved to {file_path}")



def start_article_generation(data):
    
    global WEBFLOW_API_TOKEN, COLLECTION_ID, SITE_ID

    company = data['company']
    company_name=data['companyName'],
    product_name=data['productName'],
    company_info=data['companyInfo']
    product_info=data['productInfo']
    mention_product=data['mentionProduct']
    specific_product_info=data['specificProductInfo']
    
    tone=data['tone'],
    intent=data['intent'],
    
    #Custom Keyword Generation
    keywords=data['keywords'], #This should be a list of strings
    keyword_input_type=data['keywordInputType']
    keyword_theme=data['keywordTheme']
    

    custom_instructions=data['customInstructions']
    section_count=data['sectionCount']
    wordcount_per_section=data['wordCountPerSection']
    images_per_article=int(data['imagesPerArticle'])
    article_count=data['articleCount']
    
    internal_linking=data['internalLinking']
    internal_linking_url=data['internalLinkingUrl']
    external_linking=data['externalLinking']
    
    previous_topics = [] #To ensure we don't generate on the same topic...
    if company == "MyAIFrontDesk":
        scraped_keywords = ["business internet phone service", "business phone service voip", "business voip", "small business ip phone systems", "small business voip", "voip business phone services", "voip business service", "voip business service provider", "voip business system", "voip business systems", "voip for business", "voip phone service provider", "voip phone service providers", "voip service provider", "voip service providers", "voip services providers", "voip small business", "/business/virtual-receptionist/", "1 800 number availability", "1 800 numbers for small business", "1 voip account login", "1-voip customer service", "10 customer expectations", "1800 answering service", "1800 phone number for business", "1800 phone service", "1800 vanity numbers", "1voip voicemail", "8 line phone system", "800 number companies", "800 number portability", "800 number small business", "800 number vanity", "800 vanity phone number", "855 vanity numbers", "866 numbers for sale", "8by8 phone system", "8x8 blog", "8x8 toll free numbers", "8x8 vs vonage", "Best Business Text", "Best Business Texting", "Best Business Texts", "HOW TO USE VTEXT", "Texting For Service", "V3CX T", "a business by phone number", "a call phone", "a cold transfer occurs when", "a good voicemail message", "a phone app", "a phone call", "a phone number", "acceptable jitter for voip", "acceptable voip jitter", "access voicemail att", "access voicemail from another phone verizon", "account number for porting", "activate call divert", "activate call forwarding", "activate call forwarding verizon", "add a business line to cell phone", "add a phone number to my cell phone", "add business line to cell phone", "add recipient to text iphone", "affordable small business phone system", "after business hours message", "after hour message", "after hours message", "after hours message script", "after hours phone message script", "after hours voicemail script", "ai voicemail", "all call app", "all calls recorded", "all phone calls are recorded", "alternative for google voice", "alternative google voice", "alternative to google voice", "alternative to google voice free", "alternative to google voice number", "alternatives for google voice", "alternatives to google voice", "alternatives to google voice number", "alternatives to skype for calling landlines", "american voip", "android answering machine", "android call forwarding specific numbers", "android forwarding calls", "android phone forward calls", "android record voicemail", "android text to email", "android voice message", "android voip phone app", "another name for cold calling is", "another way to say i wanted to follow up", "answer a call", "answer call", "answer cell phone on computer", "answer google voice call on computer", "answer iphone calls on pc", "answer machine greetings", "answer machine message", "answer machine messages", "answer machine messages audio", "answer machine messages for businesses examples", "answer machine voice", "answer message", "answer messages", "answer messages for phones", "answer phone call", "answer phone calls", "answer phone calls on pc", "answer phone from computer", "answer phone message", "answer phone messages", "answer phone on computer", "answer the calling", "answer your text", "answered calls"]
    else:
        scraped_keywords = ['automated description', 'AI   digital marketing', 'AI digital marketing in banking and finance', 'DIY SEO automate', 'DIY automation SEO', 'Digital Marketing Specialist- GiniMachine: AI Credit Scoring', 'How to Skyrocket Your SEO with Automated Link Building', 'SEO marketing automation', 'Using IFTTT For SEO and Automated Link Building', 'advanced voice search, digital marketing, ai', 'ai and computer vision digital marketing 2018', 'ai and digital marketing', 'ai and machine learning digital marketing', 'ai and machine learning in digital marketing', 'ai article writer', 'ai article writing', 'ai content generator', 'ai dashboard for digital marketing', 'ai digital marketing', 'ai digital marketing agency', 'ai digital marketing clipart', 'ai digital marketing companies', 'ai digital marketing new york', 'ai digital marketing stsatistics', 'ai digital marketing tools', 'ai for articles', 'ai for content creation', 'ai for digital marketing', 'ai for writing email', 'ai in digital marketing', 'ai in digital marketing 2020', 'ai learning digital marketing ireland', 'ai like chatgpt for writing', 'ai platform for digital marketing', 'ai software for digital marketers', 'ai software for digital marketing agncies', 'ai that writes papers', 'ai to write articles', 'ai tools for digital marketing', 'ai writing editor', 'ai-powered digital marketing applications', 'ais media, inc digital marketing', 'ais media, inc digital marketing landing page', 'app for writing letters', 'are automated blog posts effective for seo', 'are automated landing pages bad for seo', 'are you a digital marketer looking to work in a disruptive environment with the latest ai', 'article writer', 'article writing ai', 'artificial intelligence writer', 'artificial intelligence writing software', 'automate email report seo', 'automate iyp seo citations', 'automate local seo citations', 'automate seo', 'automate seo metrics semrush', 'automate seo reporting', 'automate seo reporting weebly', 'automate your seo', 'automate your seo to withstand google updates â€“ coreseo demo', 'automate your seo â€“ coreseo demo', 'automated SEO split testing software', 'automated ai seo', 'automated artificial intelligence seo software', 'automated content writing tools for seo', 'automated local content for seo', 'automated local seo', 'automated local seo citations', 'automated local seo software', 'automated meta tag and seo optimizer online', 'automated payment system digital downloads and seo,,,hosting', 'automated reporting seo', 'automated reporting tools seo', 'automated seo', 'automated seo analysis', 'automated seo audit', 'automated seo dashboard', 'automated seo for wordpress', 'automated seo monitoring', 'automated seo optimization', 'automated seo platform', 'automated seo plugin', 'automated seo report', 'automated seo report template', 'automated seo reporting', 'automated seo reports', 'automated seo reveiw', 'automated seo services', 'automated seo software', 'automated seo solution', 'automated seo tasks', 'automated seo testing', 'automated seo tool', 'automated seo tools', 'automated seo tools 2018', 'automated seo wordpress', 'automated seo wordpress plugin', 'automated seo writing', 'automated youtube seo', 'automating seo', 'automative seo', 'best ai content writing tools', 'best ai copywriter', 'best automated seo', 'best automated seo reporting', 'best automated seo software', 'best automated seo tools', 'best seo automation', 'best seo automation software', 'best seo automation software tools', 'best seo automation tool', 'best seo automation tools', 'best web design tools which automate seo', 'buzzfeed on page seo automation', 'cache:https://vmblog.com/archive/2019/10/07/ai-and-digital-marketing-the-numbers.aspx#.xch3f5jkium', 'can seo be automated', 'content generator ai', 'creative digital marketing and ai', 'creative digital marketing nd ai', 'digital asset manager ai market size', 'digital marketers guide to ai', 'digital marketing ai', 'digital marketing ai automated marketing', 'digital marketing ai companies', 'digital marketing and ai', 'digital marketing campaign using emotion ai', 'digital marketing in an ai world pdf', 'digital marketing manager at ai media group', 'digital marketing manager at ai media group salary', 'digital marketing powerpoint ai', 'digital marketing startegies using ai', 'digital marketing startegies using ai floe', 'digital marketing startegies using ai flow', 'digital marketing strategies: data, automation, ai & analytics', 'digital marketing using ai', 'does google allow automated seo tools', 'does squarespace automate seo', 'frederick vallaeys digital marketing in an ai world summary', 'free ai blog writer', 'free automated seo analysis for your website', 'free automated seo audit report', 'free automated seo report', 'free automated seo reports', 'free automated seo software', 'free seo automation tools', 'fully automated seo software', 'future jobs in digital marketing ai', 'future of ai in digital marketing', 'get automated backlinks with this seo', 'godaddy automated seo any good', 'healthcare, digital, ai, marketing', 'how ai is changing digital marketing', 'how ai is used in digital marketing', 'how is ai changing digital marketing', 'how is market research evolving in a digital, ai-led marketing world?', 'how is seo a part of marketing automation', 'how to automate local citation listings seo', 'how to automate seo', 'how to automate seo reports', 'how to build an automated seo blog', 'how will ai affect digital marketing', 'ia writing', 'insurance agency seo automated insurance agency', 'insurance agent seo automated insurance agency', 'is there a software that will write content pulled from multiple sources', 'is watson ai good for digital marketing?', 'joomla automated seo', 'journalist ai', 'large scale seo automation', 'lettre de motivation digital marketing franÃ§ais', 'local seo automation', 'lod ai digital marketing', 'marketing automation branded verses non-branded url and seo pro con', 'marketing automation seo', 'marketing statistics for ai digital assistants', 'need data analytics for ai and digital signage - marketing/shopper', 'professional email writer generator', 'rephrase sentence generator tool', 'robotic automation seo', 'scrapebox automator seo', 'selenium seo automation', 'senior saas and ai sales director, digital marketing (new business)', 'sentient ai digital marketing', 'seo and traffic report automation', 'seo automate metadescription', 'seo automated', 'seo automated content generation', 'seo automated services', 'seo automated software', 'seo automation', 'seo automation consortium', 'seo automation for lawyers', 'seo automation meta description', 'seo automation program', 'seo automation seo platform', 'seo automation software', 'seo automation software free', 'seo automation tasks', 'seo automation test using a selenium', 'seo automation testing', 'seo automation tool', 'seo automation tools', 'seo automation wordpress plugin', "seo google thinks i'm sending automated searches", 'seo how to build facebook followers with automated', 'seo powersuite automated email options', 'seo social media automation', 'seo tools for backlink automation', 'seo-automated-seo-tools wordpress plugin', 'serp seo automated artificial intelligence white label', 'the best software for automating your seo on html website', 'the most detailed free automated seo report online', 'top automated seo resellers', 'use of ai in digital marketing', 'using ai in digital marketing', 'using ai to write articles', 'webpagefx automative seo', 'what is ai in digital marketing', 'what is the best automated app for seo and marketing shopify', 'why automation in seo', 'will ai take over digital marketing', 'wordpress seo automation', 'writing app for computer', 'writing assistance', 'writing enhancement software', 'youtube seo automation']
    
    #Determining which website to post to
    if company == "MyAIFrontDesk":
        WEBFLOW_API_TOKEN = os.getenv("AIFD_WEBFLOW_API_KEY")
        COLLECTION_ID = os.getenv("AIFD_WEBFLOW_COLLECTION_ID")
        SITE_ID = os.getenv("AIFD_WEBFLOW_SITE_ID")
    else:
        WEBFLOW_API_TOKEN = os.getenv("WEBFLOW_API_KEY")
        COLLECTION_ID = os.getenv("WEBFLOW_COLLECTION_ID")
        SITE_ID = os.getenv("WEBFLOW_SITE_ID")
   
    
        
    print("Starting blog post creation process...")
    for article in range(article_count):
        #Finding keywords
        if keyword_input_type == 'auto':
            keywords = generate_keywords(keyword_theme)
            
        elif keyword_input_type == 'manual_test':
            keywords = scraped_keywords[:3]
            scraped_keywords = scraped_keywords[len(keywords):] #deleting the keywords we just used
        
        if len(keywords) == 0:
            print("No keywords found, skipping article generation")
            break
        
        
        print(f"Generating article number {article}")
        topic = generate_blog_topic(keywords, tone, intent, company_info, product_info, custom_instructions, previous_topics)
        previous_topics.append(topic)
        
        title, content = generate_blog_post(topic, company_name, product_name, company_info, product_info, mention_product, 
                                            specific_product_info, keywords, tone, intent, custom_instructions, internal_linking, internal_linking_url, external_linking, section_count, wordcount_per_section, images_per_article)
        
        slug = generate_slug(keywords[0], topic)
        
        print(f"Blog post generated. Title: {title}")
        print("Adding to Webflow...")
        try:
            response = create_blog_post(title, content, slug)
            print(f"Blog post added successfully.")
            print(f"This is response {response}")
            
            # try:
            #     print("Publishing to site")
                
            
            save_blog_post_info(title)
            
        except Exception as e:
            print(f"Error creating blog post: {str(e)}")
            print("Response content:", getattr(e, 'response', {}).get('content', 'No response content'))


            
if __name__ == "__main__":
    # start_article_generation()

    result = start_article_generation(am_data)
