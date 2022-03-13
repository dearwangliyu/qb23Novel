import os.path
import re
import zipfile
import requests
from lxml import etree
import shutil
import cv2
from character_to_num import chinese_to_arabic

#实例化请求会话
session = requests.session()
url = 'https://www.23qb.net'
header = {
	'User - Agent': 'Mozilla / 5.0(Windows NT 10.0;Win64;x64;rv: 97.0) Gecko / 20100101Firefox / 97.0',
}
def login():
	address = '/login.php?do=submit'
	param = {
		'username' : '君若清路尘'.encode('GBK'),
		'password': '111223',
		'action' :  'login'
	}
	result = session.post(url+address,params=param,headers=header)
	if '登录成功' in result.text:
		print('登陆成功')

def get_book_list():
	bookcase = url + '/bookcase.php'
	page_code = session.get(bookcase,headers=header)
	tree = etree.HTML(page_code.text)
	list = tree.xpath('//div[@class="r_2"]/ul/li')
	return_list = []
	for one in list:
		book_name = one.xpath('./div[2]/div[1]/a/text()')[0]
		book_url = one.xpath('./div[2]/div[1]/a/@href')[0]
		pic_url = one.xpath('./div[1]/a/img/@_src')[0]
		pic_url = url + pic_url
		book_url = url + book_url
		return_list.append({'title':book_name,'url':book_url,'pic':pic_url})
	return return_list

def get_content(book_list):
	total_dict = {}
	for list in book_list:
		total_title = list['title']
		book_url = list['url']
		page_code = session.get(book_url,headers=header)
		tree = etree.HTML(page_code.text)
		content_path = tree.xpath('//ul[@id="chapterList"]/li')
		content_list = []
		total_content_list = {}
		for cont in content_path:
			all_title = cont.xpath('./a/text()')[0]
			link = cont.xpath('./a/@href')[0]
			content_list.append({'title':all_title,'url':url + link})
		for num in content_list:
			name = num['title'].split()[0]
			if name in total_content_list.keys():
				continue
			tem_list = []
			for add in content_list:
				if name in add['title']:
					tem_list.append(add)
			total_content_list[name] = tem_list
		print(total_content_list)
		total_dict[total_title] = total_content_list
	return total_dict

def download_book(dict,book_list):
	first = 0
	for book_name in dict:#遍历书总数
		mkdir(book_name)
		line = 1
		for book_volume in dict[book_name]:#遍历卷数
			path_one = '%s\\%s'%(book_name,book_volume)
			print(book_name,book_volume)
			mkdir(path_one)
			num = 1
			all_title = []
			for book_content in dict[book_name][book_volume]:#遍历各章节
				path_two = '%s\\OEBPS\\Text'%(path_one)
				path_xhtml = '%s\\chapter%d.xhtml'%(path_two,num)
				mkdir(path_two)
				p = get_main(book_content['url'])
				title = ''.join(book_content['title'].split(' ')[1:])
				print(title)
				all_title.append(title)
				with open(path_xhtml,'w+',encoding='utf-8') as w:
					w.write(xhtml(title,p))
				num += 1
			all_num = num - 1
			unzip('epub.zip',path_one)#解压epub所需文件
			pic = session.get(book_list[first]['pic'],headers=header)
			with open(f'cover.jpg','wb+') as c:
				c.write(pic.content)
			f1 = re.findall('[1-9]',book_volume)
			f2 = re.findall('第([一-龟]*)卷',book_volume)
			if f1 != []:
				f1 = re.findall('第(.*)卷', book_volume)
				line_cover(float(f1[0]),'cover.jpg')
			elif f2 != []:
				line_cover(chinese_to_arabic(f2[0]), 'cover.jpg')
			shutil.move('cover.jpg',f'{path_one}\\OEBPS\\Images\\cover.jpg')
			with open(f'{path_one}\\OEBPS\\content.opf','w+',encoding="utf-8") as o:
				o.write(content(all_num,book_name,book_volume))
			with open(f'{path_one}\\OEBPS\\toc.ncx','w+',encoding="utf-8") as o:
				o.write(toc(all_num,all_title,book_name,book_volume))
			with open(f'{path_one}\\OEBPS\\Text\\contents.xhtml','w+',encoding="utf-8") as c:
				c.write(contents(all_num,all_title))
			shutil.make_archive(path_one,'zip',path_one)
			shutil.move(f'{path_one}.zip',f'{path_one}.epub')
			line += 1
	first += 1

def xhtml(title,passage):
	formwork = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head>
  <link href="../Styles/style.css" rel="stylesheet" type="text/css"/>
  <title>{0}</title>
</head>
<body>
  <div class="article">
	<h1>{0}</h1>
	{1}
  </div>
</body>
</html>'''.format(title,passage)
	return formwork

def content(page_num,book_name,book_volume):
	part_spine = ''
	part_manifest = ''
	for num in range(page_num):
		part_spine += f'<itemref idref="chapter{num+1}.xhtml"/>\n'
		part_manifest += f'<item id="chapter{num+1}.xhtml" href="Text/chapter{num+1}.xhtml" media-type="application/xhtml+xml"/>\n'
	content =f'''<?xml version="1.0" encoding="utf-8"?>
<package version="2.0" unique-identifier="BookId" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:opf="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId" opf:scheme="UUID">urn:uuid:5208e6bb-5d25-45b0-a7fd-b97d79a85fd4</dc:identifier>
    <dc:title>{book_name} {book_volume}</dc:title>
    <dc:language>zh-CN</dc:language>
    <dc:description></dc:description>
    <meta name="cover" content="cover.jpg" />
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="cover.xhtml" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>
    <item id="style.css" href="Styles/style.css" media-type="text/css"/>
    <item id="cover.jpg" href="Images/cover.jpg" media-type="image/jpeg"/>
    <item id="contents.xhtml" href="Text/contents.xhtml" media-type="application/xhtml+xml"/>
    {part_manifest}
  </manifest>
  <spine toc="ncx">
    <itemref idref="cover.xhtml" properties="duokan-page-fullscreen"/>
    <itemref idref="contents.xhtml"/>
    {part_spine}
  </spine>
  <guide>
    <reference type="toc" title="contents" href="Text/contents.xhtml"/>
    <reference type="cover" title="cover" href="Text/cover.xhtml"/>
  </guide>
</package>
'''
	return content

def toc(page_num,all_title,title,book_volume):
	nav = ''
	for num in range(page_num):
		nav += f'''
		<navPoint id="navPoint-{num+4}" playOrder="{num+4}">
        <navLabel>
          <text>第{num+1}话 {all_title[num]}</text>
        </navLabel>
        <content src="Text/chapter{num+1}.xhtml"/>
      </navPoint>'''
	toc = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
   "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:5208e6bb-5d25-45b0-a7fd-b97d79a85fd4"/>
    <meta name="dtb:depth" content="2"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>{title} {book_volume}</text>
  </docTitle>
  <navMap>
    <navPoint id="navPoint-1" playOrder="1">
      <navLabel>
        <text>封面</text>
      </navLabel>
      <content src="Text/cover.xhtml"/>
    </navPoint>
    <navPoint id="navPoint-2" playOrder="2">
      <navLabel>
        <text>目录</text>
      </navLabel>
      <content src="Text/contents.xhtml"/>
    </navPoint>
    <navPoint id="navPoint-3" playOrder="3">
      <navLabel>
        <text>正文</text>
      </navLabel>
      <content src="Text/chapter1.xhtml"/>
      {nav}
    </navPoint>
  </navMap>
</ncx>
'''
	return toc

def contents(page_num,all_title):
	tr = ''
	for num in range(page_num):
		tr += f'''
		<tr>
      				<td class="center pbt03 w44"><a class="colorg nodeco" href="../Text/chapter{num+1}.xhtml">第{num+1}话</a></td>
      				<td class="left pbt03"><a class="colorg nodeco" href="../Text/chapter{num+1}.xhtml">{all_title[num]}</a></td>
    			</tr>'''
	content = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head>
  <link href="../Styles/style.css" rel="stylesheet" type="text/css"/>
  <title>目录</title>
</head>
<body>
	<div class="contents">
		<table class="tdcenter">
  			<tbody>
    			<tr>
      				<td class="conttitle" colspan="2">CONTENTS</td>
    			</tr>
    			{tr}
  			</tbody>
		</table>
  </div>
</body>
</html>'''
	return content

def line_cover(num,path):
	img = cv2.imread(path)
	num = float(num)
	if 	num < 10:
		circle_middle = (18, 18)
		circle_radius = 15
		color = (246, 195, 79)
		white = (255, 255, 255)
		thickness = -1  # 无边框
		text_font = cv2.FONT_HERSHEY_DUPLEX
		cv2.circle(img, circle_middle, circle_radius, color, thickness)
		cv2.circle(img, circle_middle, circle_radius, white, 2)
		cv2.putText(img, str(num), (8, 27), text_font, 1, white, 1)
	elif num >= 10:
		circle_middle = (20, 20)
		circle_radius = 17
		color = (246, 195, 79)
		white = (255, 255, 255)
		thickness = -1  # 无边框
		text_font = cv2.FONT_HERSHEY_DUPLEX
		cv2.circle(img, circle_middle, circle_radius, color, thickness)
		cv2.circle(img, circle_middle, circle_radius, white, 2)
		cv2.putText(img, str(num), (5, 27), text_font, 0.7, white, 1)
	cv2.imwrite(path, img)
	cv2.waitKey(0)

def	get_main(url):
	new_url = url[:-5] + '_2.html'
	page_code = session.get(new_url,headers=header)
	tree = etree.HTML(page_code.text)
	title = tree.xpath('//div[@id="mlfy_main_text"]/h1/text()')[0]
	times = int(re.findall('（.*/(.*)）',title)[0])
	content = ''
	num = 1
	p = ''
	while num <= times:
		so_url = '%s_%d.html'%(url[:-5],num)
		page_source = session.get(so_url,headers=header)
		find_p_compile = re.compile(r'<div id="mlfy_main_text">[\s\S]*?(<p>[\s\S]*</p>)<p>铅[\s\S]*?</div>')
		find_p = re.findall(find_p_compile,page_source.text)
		out = re.sub('<.?p>','',''.join(find_p))
		print(out)
		p += find_p[0]
		num += 1
	replace = re.compile('<p style.*?>（继续下一页）<\/p>',re.S)
	p = re.sub(replace,'',p)
	return p


def mkdir(path):
	if not os.path.exists(path):
		os.makedirs(path)

def unzip(file,path):
	zip_file = zipfile.ZipFile(file)
	zip_list = zip_file.namelist()  # 得到压缩包里所有文件
	for f in zip_list:
		zip_file.extract(f, path)  # 循环解压文件到指定目录
	zip_file.close()


if __name__ == '__main__':
	login()
	book_list = get_book_list()
	dict = get_content(book_list)
	download_book(dict,book_list)