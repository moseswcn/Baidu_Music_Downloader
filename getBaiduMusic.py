#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import os
import requests
import urllib2
import re
import platform
from BeautifulSoup import BeautifulSoup
from system_encoding import DEFAULT_ENCODING

GLOBAL_VARIABLE = dict()
HAVEDOWNLOADED = list()

def downloadMusic(musicName, musicId):
	url = 'http://music.baidu.com/song/' + musicId + '/download'
	print url
	musicObject = requests.get(url)
	if musicObject.status_code == 200:
		musicSoup = BeautifulSoup(musicObject.content)
		downloadItem = musicSoup.find('div', attrs={'class': 'operation clearfix'}).find('a')
		if downloadItem['href']:
			downloadUrl = downloadItem['href'].replace('/data/music/file?link=', '')
			if platform.system() == 'Linux':
				downloadCmd = 'wget ' + downloadUrl + ' -O ' + GLOBAL_VARIABLE['savePath'] + \
					os.sep + musicName + '.mp3'
				downloadCmd = downloadCmd.encode(DEFAULT_ENCODING)
				os.system(downloadCmd)
				HAVEDOWNLOADED.append(musicName)
			else:
				print musicName, downloadUrl
				try:
					req = urllib2.Request(downloadUrl)
					response = urllib2.urlopen(req)
					with open(GLOBAL_VARIABLE['savePath'] + os.sep + musicName +'.mp3', 'wb') \
					as musicHandler:
						musicHandler.write(response.read())
					HAVEDOWNLOADED.append(musicName)
				except Exception, e:
					print e.message


def downloadLRC(musicName, musicId):
	url = 'http://music.baidu.com/song/' + musicId + '/lyric'
	lrcObject = requests.get(url)
	if lrcObject.status_code == 200:
		lrcSoup = BeautifulSoup(lrcObject.content)
		downloadItem = lrcSoup.find('a', attrs={'class': 'down-lrc-btn'})
		if downloadItem:
			downloadUrl = downloadItem['href']
			print 'LRC: ', downloadUrl
			if platform.system() == 'Linux':
				cmd = 'wget ' + downloadUrl + ' -O ' + GLOBAL_VARIABLE['savePath'] + \
					os.sep + musicName + '.lrc'
				cmd = cmd.encode(DEFAULT_ENCODING)
				os.system(cmd)
			else:
				try:
					req = urllib2.Request(downloadUrl)
					response = urllib2.urlopen(req)
					with open(GLOBAL_VARIABLE['savePath'] + os.sep + musicName + '.lrc', 'w') \
					as lrcHandler:
						lrcHandler.write(response.read())
				except Exception, e:
					print e.message


def getSearchResultNum(searchFirstPageResult):
	soup = BeautifulSoup(searchFirstPageResult)
	return soup.find('span', attrs={'class': 'number'}).text


def parseMusicList(musicListPageContent):
	soup = BeautifulSoup(musicListPageContent)
	musicItemList = soup.findAll('div', attrs={'class': 'song-item clearfix'})
	for musicItem in musicItemList:
		author_list = musicItem.find('span', attrs={'class' : 'author_list'})['title'].split(',')
		if GLOBAL_VARIABLE['singerName'] in author_list:
			music = musicItem.find('span', attrs={'class' : 'song-title'}).find('a')
			musicTitle = music.text.strip().replace("#", "").replace(' ', '_')
			if not musicTitle in HAVEDOWNLOADED:
				musicId = music['href'].split('/')[-1]
				downloadMusic(musicTitle, musicId)
				downloadLRC(musicTitle, musicId)


def parseAlbumList(albumPageContent):

	def downloadAlbum(albumUrl):
		albumObject = requests.get(albumUrl)
		if albumObject.status_code == 200:
			albumSoup = BeautifulSoup(albumObject.content)
			albumItems = albumSoup.findAll('div', attrs={'class': 'song-item'})
			for albumItem in albumItems:
				music = albumItem.find('span', attrs={'class': 'song-title'}).find('a')
				if music:
					musicName = music.text.strip().replace(' ', '_')
					musicId = music['href'].replace('/song/', '')
					downloadMusic(musicName, musicId)
					downloadLRC(musicName, musicId)

	soup = BeautifulSoup(albumPageContent)
	albumList = soup.findAll('div', attrs={'class': 'title clearfix'})
	for albumItem in albumList:
		album = albumItem.find('a', attrs={'href': re.compile('/album/\d+$')})
		albumName = album.text.strip().replace(' ', '_')
		for punc in ['《', '》', '(', ')', '（', '）']:
			albumName = albumName.replace(punc.decode('utf-8'), '')
		albumUrl = 'http://music.baidu.com/' + album['href']
		basePath = GLOBAL_VARIABLE['savePath']
		GLOBAL_VARIABLE['savePath'] += os.sep + albumName
		if not os.path.exists(GLOBAL_VARIABLE['savePath']):
			os.mkdir(GLOBAL_VARIABLE['savePath'])
		downloadAlbum(albumUrl)
		GLOBAL_VARIABLE['savePath'] = basePath


def searchSingerMusic(singerName, album=False):
	url = 'http://music.baidu.com/search?key=' + singerName
	print url
	if album:
		url = 'http://music.baidu.com/search/album?key=' + singerName

	pageObject = requests.get(url)
	if pageObject.status_code == 200:
		if album:
			totalNum = int(getSearchResultNum(pageObject.content))
			parseAlbumList(pageObject.content)
			start, size = 10, 10
			while start < totalNum:
				url = 'http://music.baidu.com/search/album?key=' + singerName + '&start=' + \
					str(start) + '&size=' + str(size)
				pageObject = requests.get(url)
				parseAlbumList(pageObject.content)
				start += size
		else:
			totalNum = int(getSearchResultNum(pageObject.content))
			parseMusicList(pageObject.content)
			start, size = 20, 20
			while start < totalNum:
				url = 'http://music.baidu.com/search/song?key=' + singerName + '&start=' + \
					str(start) + '&size=' + str(size)
				pageObject = requests.get(url)
				parseMusicList(pageObject.content)
				start += size


def main():
	album = False
	dirname = ''
	# 如果要下载专辑而不是单曲，则加-a选项
	if '-a' in sys.argv:
		album = True
	# 如果加了-d选项，则该选项的后一个列表项即为存储音乐的父目录名
	if '-d' in sys.argv:
		dirname = sys.argv[sys.argv.index('-d') + 1]
		if not dirname.endswith(os.sep):
			dirname += os.sep
	# 命令行的第二个参数是歌手的姓名
	singerName = sys.argv[1]
	savePath = dirname + singerName.replace(' ', '_')
	if not os.path.exists(savePath):
		os.mkdir(savePath)

	GLOBAL_VARIABLE['savePath'] = unicode(savePath, DEFAULT_ENCODING)
	GLOBAL_VARIABLE['singerName'] = unicode(singerName, DEFAULT_ENCODING)

	singerName = singerName.decode(DEFAULT_ENCODING).encode('utf-8')
	searchSingerMusic(singerName, album = album)

if __name__ == '__main__':
	main()