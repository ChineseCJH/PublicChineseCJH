# Include
import requests # Request website
from bs4 import BeautifulSoup # Parsing the HTML of a website
from threading import Thread # Multi-threaded requests for websites
import time # Access time
import math # Get the number of threads
import re # Parsing Web Pages with Regular Expressions
import sys # system function
import os # file operation

# Class MyThread
class MyThread(Thread):
    def __init__(self, func, args):
        '''
        :param func: 可调用的对象
        :param args: 可调用对象的参数
        '''
        Thread.__init__(self)
        self.func = func
        self.args = args
        self.result = None

    def run(self):
        self.result = self.func(*self.args)

    def getResult(self):
        return self.result

# Save posts and pastes
def SavePost(username,ojurl,headers):
    try:
        os.mkdir('Post')
    except FileExistsError:
        pass
    print('Start getting the list of your posts')
    fp = r'<a\s+href="https:\/\/qoj\.fzoi\.top\/post\/(\d+)">'
    res = requests.get(ojurl+'/user/post/'+username, headers = headers, timeout = 30)
    post_list = re.findall(fp,res.text)
    res = requests.get(ojurl+'/pastes', headers = headers, timeout = 60)
    post_list += re.findall(fp,res.text)
    print('Finish getting the list of your posts')
    print('Start getting your posts')
    for postid in post_list:
        res = requests.get(ojurl+'/post/'+str(postid)+'/write', headers = headers, timeout = 60)
        title_tag = BeautifulSoup(res.text, 'html.parser').find('input',{'name':'post_title'})
        title = title_tag['value']
        # The filename must not contain \/:*?"<>|
        filename = str(postid) + ' - ' + title.replace('\\','_').replace('/','_').replace(':','_').replace('*','_').replace('?','_').replace('"','_').replace('<','_').replace('>','_').replace('|','_') +'.md'
        filepath = os.path.join('Post',filename)
        
        text_tag = BeautifulSoup(res.text, 'html.parser').find('textarea', {'name': 'post_content_md'})
        prettified_html = BeautifulSoup(text_tag.prettify(), 'html.parser')
        text = prettified_html.get_text(separator='\n').replace('\r','')
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        with open(filepath,'w',encoding='utf-8') as f:
            f.write(text)
        # print(text)
        print('Finish saving post',filename)

# Save submissions



def SaveSubmissions(username,ojurl,headers):
    freelist = []
    
    problems = 2000
    cnt = problems
    
    def SaveProblem(username,ojurl,problem_id,headers,thnum):
        nonlocal freelist,cnt
        for _ in range(3):
            try:
                res = requests.get(ojurl+'/submissions?problem_id='+str(problem_id)+'&submitter='+username,headers = headers, timeout = 30)
                break
            except:
                time.sleep(5000)
                continue
        sublist = []
        errorlist = []
        if '无' in res.text:
            freelist.append(thnum)
            cnt -= 1
            return (problem_id,errorlist)
        else:
            try:
                os.mkdir('Submission/'+str(problem_id))
            except FileExistsError:
                pass
            # Get list
            fp = r'<a\s+href="\/submission\/(\d+)">#'
            sublist = re.findall(fp,res.text)
            if '<a class="page-link" href="/submissions?problem_id='+str(problem_id)+'&amp;submitter='+username+'">1</a>' in res.text:
                for page in range(2,501):
                    for _ in range(3):
                        try:
                            res = requests.get(ojurl+'/submissions?problem_id='+str(problem_id)+'&submitter='+username+'&page='+str(page),headers = headers, timeout = 30)
                            break
                        except:
                            time.sleep(5000)
                            continue
                    page_url = '<a class="page-link" href="/submissions?problem_id='+str(problem_id)+'&amp;submitter='+username+'&amp;page='+str(page)+'">'+str(page)+'</a>'
                    if page_url not in res.text:
                        break
                    sublist += re.findall(fp,res.text)

            sp = r'<a href="/submission/\d+" class="uoj-score">(\d+)</a>'
            for sub in sublist:
                for _ in range(3):
                    try:
                        res = requests.get(ojurl+'/submission/'+str(sub), headers = headers, timeout = 30)
                        break
                    except:
                        time.sleep(5000)
                        continue
                score_list = re.findall(sp,res.text)
                if 'Compile Error' in res.text:# CE
                    score = 'Compile Error'
                elif 'Judgement Failed' in res.text:# JF
                    score = 'Judgement Failed'
                elif score_list:# Get score
                    score = int(score_list[0])
                else:
                    continue
                if '<code ' not in res.text:
                    continue
                try:
                    soup = BeautifulSoup(res.text,'html.parser')
                    code_tag = soup.find('code')
                    code = code_tag.string.replace('\r','').replace('\n\n','\n')
                    code_last = code_tag['class'][0][3:]# language
                    filename = sub+' - '+str(score)
                    if code_last == 'cpp':
                        filename+='.cpp'
                    elif code_last == 'c':
                        filename+='.c'
                    elif code_last == 'python':
                        filename+='.py'
                    elif code_last == 'pascal':
                        filename+='.pas'
                    else:
                        filename+='.'+code_last
                    folder_path = os.path.join('Submission', str(problem_id))
                    output_path = os.path.join(folder_path,filename)
                    with open(output_path,'w',encoding = 'utf-8') as f:
                        f.write(code)
                except:
                    errorlist.append(sub)
        freelist.append(thnum)
        cnt -= 1
        return (problem_id,errorlist)
    try:
        os.mkdir('Submission')
    except FileExistsError:
        pass

    errorlist = []

    thcnt = min(5,problems)

    t = [MyThread(SaveProblem,(username,ojurl,i+1,headers,i)) for i in range(thcnt)]

    for i in range(thcnt):
        print('Start getting the submissions of the problem',i+1)
        t[i].start()
    for i in range(thcnt,problems):
        while not freelist:
            pass
        now = freelist.pop()
        t[now].join()
        result = t[now].getResult()
        for sub in result[1]:
            print(f'An error occurred while saving submission {sub}.')
        errorlist += result[1]
        print('Finish getting the submissions of the problem',result[0])
        t[now] = MyThread(SaveProblem,(username,ojurl,i+1,headers,now))
        t[now].start()
        print('Start getting the submissions of the problem',i+1)
    start_time = time.time()
    while time.time()-start_time<=60 and (cnt or freelist):
        if freelist:
            now = freelist.pop()
            t[now].join()
            result = t[now].getResult()
            for sub in result[1]:
                print(f'An error occurred while saving submission {sub}.')
            errorlist += result[1]
            print('Finish getting the submissions of the problem',result[0])
    
    filepath = os.path.join('Submission','error.txt')
    with open(filepath,'w',encoding='utf-8') as f:
        for sub in errorlist:
            f.write('#'+str(sub)+'\n')

# Main
def main():
    print('Input username:')
    username = input()
    print('Input cookie:')
    cookie = input()

    ojurl = 'https://qoj.fzoi.top'
    

    headers = {
        'cookie':cookie,
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188',
    }
    
    
    print('Start getting your Chinese name')
    for _ in range(3):
        try:
            res = requests.get(ojurl+'/user/profile/'+username, headers = headers, timeout = 30).text
            break
        except:
            time.sleep(5000)
            continue
    span_tag = BeautifulSoup(res, 'html.parser').find('span',class_='uoj-honor')
    ChineseName = span_tag.text
    print('Finish getting your Chinese name')
    print('Your Chinese name is',ChineseName)

    print('Do you need save posts (with pastes)(Y/N)?')
    RunFunc = input()
    if RunFunc=='Y':
        SavePost(username,ojurl,headers)

    print('Do you need save your submissions(Y/N)?')
    RunFunc = input()
    if RunFunc=='Y':
        SaveSubmissions(username,ojurl,headers)
    

if __name__=='__main__':
    main()
