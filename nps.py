import scrapy

#run with: scrapy crawl nps -o NPS_research_summaries.csv

class NpsSpider(scrapy.Spider):
    name = 'nps'
    start_urls = ['https://nps.edu/web/research/search?q=of&delta=200']

    #when the "publications" or "data" field is empty, it will say this
    field_is_empty_text = "Publications, theses (not shown) and data repositories will be added to the portal record when information is available in FAIRS and brought back to the portal"

    def parse_single_summary(self, response):    

        title = response.xpath('//*[@id="portlet_edu_nps_researchsummaries_ResearchSummariesController"]/div/div[2]/div/div[1]/h3/span[2]/text()').get()
        title = title.strip().replace('\n', ' ').replace('\t','')

        final_labels = []
        final_data_strs = []
        table_rows = response.xpath("//table/tbody/tr")
        #print("number of table_rows = ", len(table_rows))
        for r in table_rows:
            #get labels. no need to read over the top of <br>
            label_text = r.xpath(".//td[@class='table-cell first']/text()").get()
            label_text = label_text.strip()
            

            data_text = r.xpath(".//td[@class='table-cell last']/text()").extract()
            final_data_string = ""

            if label_text == 'Fiscal Year' or label_text == 'Division' or label_text == 'Department' or label_text == 'Sponsor' or label_text == 'Keywords':
                for dt in data_text: #there will likely only be one element in the array for this field, but looping just in case
                    if not dt.isspace(): #ignore the element if it is just white space
                        final_data_string += dt.strip().replace(',','').replace('\n', ' ').replace('\t','')
            elif label_text == 'Investigator(s)':
                first_name = True
                for dt in data_text:
                    if not dt.isspace(): #ignore elements in text (string array) that are only whitespace with no text
                        #strip whitespace from ends and replace any remaining whitespace in middle with spaces
                        #strip only deletes whitespace from begining and end of string. Not the middle.
                        if not first_name:
                            final_data_string += "/"
                        final_data_string += dt.strip().replace('\n', ' ').replace('\t',' ').replace(',','')
                        first_name = False
            elif label_text == 'Summary':
                for dt in data_text:
                    if not dt.isspace(): #ignore elements in text (string array) that are only whitespace with no text
                        #strip whitespace from ends and replace any remaining whitespace in middle with spaces
                        #strip only deletes whitespace from begining and end of string. Not the middle. 
                        final_data_string += " " + dt.strip().replace('\n', ' ').replace('\t',' ')
                
                #remove unwanted punctuation 
                final_data_string = final_data_string.replace(',',' ') #must do this to strore in CSV format
                final_data_string = final_data_string.replace('.',' ')
                final_data_string = final_data_string.replace("(",' ')
                final_data_string = final_data_string.replace(')',' ')
                final_data_string = final_data_string.lower()
            elif label_text == 'Keywords':
                for dt in data_text: #there will likely only be one element in the array for this field, but looping just in case
                    if not dt.isspace(): #ignore the element if it is just white space
                        final_data_string += dt.strip() + " "

                final_data_string = final_data_string.replace(',', ' ')
            elif label_text == 'Publications' or label_text == 'Data':
                for dt in data_text: #there will likely only be one element in the array for this field, but looping just in case
                    if not dt.isspace(): #ignore the element if it is just white space
                        final_data_string += dt.strip() + " "

                if final_data_string == (self.field_is_empty_text + " "):
                    final_data_string = ""

                final_data_string = final_data_string.replace(',', ' ')

            final_labels.append(label_text)
            final_data_strs.append(final_data_string)

        yield{
            "Title" : title,
            "Fiscal Year" : final_data_strs[0],
            "Division" : final_data_strs[1],
            "Department" : final_data_strs[2],
            "Investigator(s)" : final_data_strs[3],
            "Sponsor" : final_data_strs[4],
            "Summary" : final_data_strs[5],
            "Keywords" : final_data_strs[6],
            "Publications" : final_data_strs[7],
            "Data" : final_data_strs[8],
            "Url" : response.url
        }

    def parse(self, response):
        #grab each article link on current page
        for summary_link in response.xpath("//*[@id='_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_5IrM3hBhFz0k_searchContainerTagSearchContainer']/ul/li/div[2]/h4/a/@href").getall():
            yield scrapy.Request(url = summary_link, callback = self.parse_single_summary) #parse individual summary table in parse_single_summary funtion above

        #go to next page
        next_page = response.xpath("//*[@id='_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_5IrM3hBhFz0k_searchContainerTagPageIteratorBottom']/ul/li[last()]/a/@href").get()
        if next_page != "javascript:;": #if there is a next page
            yield scrapy.Request(url = next_page, callback = self.parse) #recursive call to parse function to get results off next page
        else:
            print("no next page")