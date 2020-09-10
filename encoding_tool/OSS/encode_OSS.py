
import xml.etree.ElementTree as ET
from collections import defaultdict
import os
import pandas as pd
from lxml import etree

# Months
months = {
	1: "January",
	2: "February",
	3: "March",
	4: "April",
	5: "May",
	6: "June",
	7: "July",
	8: "August",
	9: "September",
	10: "October",
	11: "November",
	12: "December"
}
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Creates initials from a name. If the name has a comma in it, it splits the comma
# and then puts the first part of the first comma behind everything else. It then takes
# the first letter of each part of the name for the initials.
def create_initials(name):
	if pd.isnull(name): return ""
	if "(" in name:
		name = name.replace("(", "").replace(")", "").replace(",", "")
	name = name.lower()
	if "," in name:
		parts = name.split(",")
		for i in range(0, len(parts)): parts[i] = parts[i].strip()
		name = "{} {}".format(" ".join(parts[1:]), parts[0])
	initials = ""
	parts = name.split(" ")
	for p in parts:
		initials = "{}{}".format(initials, p[0])
	
	return initials

# Reads the metadata to collect information on each of the files.
def read_metadata(file):
	df = pd.read_csv(file, encoding = "utf-8", header = None)

	info = {}
	for i, r in df.iterrows():
		if r[3] == "OSS":
			interviewee = r[7]
			info[interviewee] = {}
			info[interviewee]["interviewee"] = interviewee
			info[interviewee]["filename"] = r[6]
			info[interviewee]["interviewee_init"] = create_initials(r[7])
			info[interviewee]["interviewer"] = r[8]
			info[interviewee]["interviewer_init"] = create_initials(r[8])
			info[interviewee]["date"] = r[9]
			info[interviewee]["language_id"] = "eng"
			info[interviewee]["language"] = "English"
			info[interviewee]["publisher"] = "Oklahoma State University Library"

	return info

# Writes the "titleStmt" section of the TEI file, which is under "fileDesc."
def write_title_section(file_desc, info):
	title_stmt = ET.SubElement(file_desc, "titleStmt")

	# Title of the interview
	title = ET.SubElement(title_stmt, "title")
	title.text = info["title"]

	# Interviewee
	author = ET.SubElement(title_stmt, "author")
	interviewee = ET.SubElement(author, "name", id = info["interviewee_init"], reg = info["interviewee"], type = "interviewee")
	interviewee.text = info["interviewee"]

	# Interviewer
	resp_stmt = ET.SubElement(title_stmt, "respStmt")
	resp = ET.SubElement(resp_stmt, "resp")
	resp.text = "Interview conducted by "
	interviewer = ET.SubElement(resp_stmt, "name", id = info["interviewer_init"], reg = info["interviewer"], type = "interviewer")
	interviewer.text = info["interviewer"]

	# Encoder (me!) -- I just hard-coded this in
	resp_stmt2 = ET.SubElement(title_stmt, "respStmt")
	resp2 = ET.SubElement(resp_stmt2, "resp")
	resp2.text = "Text encoded by "
	encoder = ET.SubElement(resp_stmt2, "name", id = "hs")
	encoder.text = "Hilary Sun"

# Writes the "sourceDesc" section of the TEI file, which is under "fileDesc."
def write_source_description(file_desc, info):
	source_desc = ET.SubElement(file_desc, "sourceDesc")
	bibl_full = ET.SubElement(source_desc, "biblFull")
	title_stmt2 = ET.SubElement(bibl_full, "titleStmt")
	title2 = ET.SubElement(title_stmt2, "title")
	title2.text = info["title"]
	author2 = ET.SubElement(title_stmt2, "author")
	author2.text = info["interviewee"]
	extent = ET.SubElement(bibl_full, "extent")
	publisher_stmt = ET.SubElement(bibl_full, "publicationStmt")
	publisher = ET.SubElement(publisher_stmt, "publisher")
	publisher.text = info["publisher"]
	pub_place = ET.SubElement(publisher_stmt, "pubPlace")
	date = ET.SubElement(publisher_stmt, "date")
	date.text = info["date"]

	return extent

# Writes the "fileDesc" section of the TEI file, which is under "teiHeader."
def write_file_description(header, info):
	file_desc = ET.SubElement(header, "fileDesc")
	write_title_section(file_desc, info)
	extent = write_source_description(file_desc, info)

	return extent

# Writes the "profileDesc" section of the TEI file, which is under "teiHeader."
def write_profile_description(header, info):
	profile_desc = ET.SubElement(header, "profileDesc")
	lang_usage = ET.SubElement(profile_desc, "langUsage")
	language = ET.SubElement(lang_usage, "language", id = info["language_id"])
	language.text = info["language"]

# Writes the "revisionDesc" section of the TEI file, which is under "teiHeader."
def write_revision_description(header, info):
	revision_desc = ET.SubElement(header, "revisionDesc")

# Parses the XML file.
def parse_file(file, info):
	doc = etree.parse(file)
	interviews = doc.xpath("/metadata/record")

	num = 0
	for interview in interviews:
		done = False
		interviewee = interview.find("creator").text
		interviewee_parts = []
		for part in interviewee.split(";")[0].split(","):
			if "19" not in part: interviewee_parts.append(part)
		interviewee = ",".join(interviewee_parts).strip()
		int_info = info[interviewee]
		int_info["title"] = interview.find("title").text
		root = ET.Element("TEI.2")
		header = ET.SubElement(root, "teiHeader", name = "O-STATE Stories")
		extent = write_file_description(header, int_info)

		# Creates the text itself
		text = ET.SubElement(root, "text")
		body = ET.SubElement(text, "body")
		div1 = ET.SubElement(body, "div1", type = "about_interview")
		div2 = ET.SubElement(body, "div2")

		nodes = interview.find("structure").find("node").findall("node")
		total_pages = 0
		for n in nodes:
			boilerplate_sep = [
				"This is Julie Pearson-Little Thunder",
				"My name is Julie Pearson-Little Thunder",
				"I   m visiting with Melvin Wade this afternoon.", 
				"Please say your name, and spell your first and last name.",
				"If you wouldn   t mind, could you each say your name and spell it for me?",
				"Today is Monday, April 4,  2016",
				"My name is Jennifer  Paustenbaugh",
				"Hello and thank you for agreeing to participate in this oral history project",
				"My name is Jerry Gill",
				"My name is Karen Neurohr",
				"This is Sarah Milligan",
				"I   m  with the OSU Library",
				"My  name is Jennifer Paustenbaugh",
				"This is Jennifer Paustenbaugh",
				"Today is Thursday, October 4, 2007",
				"It is Saturday, April 18, 2009",
				"Thank you for agreeing to participate in this Oral History project",
				"Okay, we   ll start with some introductions here",
				"Today is Friday, October 17th",
				"First off, this is Sarah Milligan",
				"It is Friday morning, October 17, 2008",
				"Today is Saturday, April 18, 2009.",
				"I   m Jerry Gill",
				"This is Monday, April 16",
				"My name is Juliana Nykolaiszyn with the Oklahoma State University  Library",
				"Thank you for agreeing to participate in this oral history project, Miss Alexander",
				"This is Sarah Milligan with the Oklahoma Oral History Research Program",
				"Today is September 28th, 2007",
				"Again, thank you for agreeing to participate in this Oral History Project",
				"It is Saturday, October 21, 2006, and my name is Jennifer Paustenbaugh",
				"Ms. Malav  , thank you for agreeing to participate in this oral history project",
				"The  interviewer is Victor Dominguez Baeza, which is myself, Director of Library  Graduate Services."
			]

			pages = n.findall("page")
			for i in range(1, len(pages) + 1):
				pb = ET.SubElement(div2, "pb", id = "p{}".format(total_pages + i), n = str(total_pages + i))
			total_pages += len(pages)
			if n.find("nodetitle").text != "Transcript": continue
			transcript = n.find("page").find("pagetext").text
			interviewers = int_info["interviewer"].split(";")
			for i in interviewers:
				i = i.strip()
				i_parts = i.split(",")
				boilerplate_sep.append("My name is {} {}".format(i_parts[1].replace("Jr.", "").strip(), i_parts[0].replace("Jr.", "").strip()).replace(" C. ", " ")),
				boilerplate_sep.append("My name is {} {}".format(i_parts[1].replace("Jr.", "").strip(), i_parts[0].replace("Jr.", "").strip()).replace(" C. ", " ")),
				boilerplate_sep.append("Okay, so this is {} {}".format(i_parts[1].replace("Jr.", "").strip(), i_parts[0].replace("Jr.", "").strip()).replace(" C. ", " ")),
				boilerplate_sep.append("This is {} {}".format(i_parts[1].replace("Jr.", "").strip(), i_parts[0].replace("Jr.", "").strip()).replace(" C. ", " ")),
				boilerplate_sep.append("I am {} {}".format(i_parts[1].replace("Jr.", "").strip(), i_parts[0].replace("Jr.", "").strip()).replace(" C. ", " ")),
				boilerplate_sep.append("All right, so this is {} {}".format(i_parts[1].replace("Jr.", "").strip(), i_parts[0].replace("Jr.", "").strip()).replace(" C. ", " "))
				boilerplate_sep.append("I   m {} {}".format(i_parts[1].replace("Jr.", "").strip(), i_parts[0].replace("Jr.", "").strip()).replace(" C. ", " "))

			dates = int_info["date"].split(",")
			for d in dates:
				d = d.strip()
				date_parts = d.split("/")
				boilerplate_sep.append("Today is {} {}, {}".format(months[int(date_parts[0])], date_parts[1], date_parts[2]))
				boilerplate_sep.append("This is {} {}, {}".format(months[int(date_parts[0])], date_parts[1], date_parts[2]))
				boilerplate_sep.append("It   s {} {}, {}".format(months[int(date_parts[0])], date_parts[1], date_parts[2]))
				for day in days:
					boilerplate_sep.append("Today is {}, {} {}, {}".format(day, months[int(date_parts[0])], date_parts[1], date_parts[2]))
					boilerplate_sep.append("This is {}, {} {}, {}".format(day, months[int(date_parts[0])], date_parts[1], date_parts[2]))
					boilerplate_sep.append("It   s {}, {} {}, {}".format(day, months[int(date_parts[0])], date_parts[1], date_parts[2]))
				

			int_parts = interviewee.split(",")
			boilerplate_sep.append("The following interview is being conducted with Ms. {} {}".format(int_parts[1].strip(), int_parts[0].strip()))
			boilerplate_sep.append("I   m  interviewing {} {}".format(int_parts[1].strip(), int_parts[0].strip()))
			
			text = transcript
			for sep in boilerplate_sep:
				if sep in transcript:
					parts = transcript.split(sep)
					head = ET.SubElement(div1, "head")
					head.text = parts[0]
					text = "{}{}".format(sep, sep.join(parts[1:]))
					num += 1
					done = True
					break
			paragraph = ET.SubElement(div2, "p")
			paragraph.text = text

		extent.text = str(total_pages)

		tree = ET.ElementTree(root)
		tree.write("{}.tei".format(int_info["filename"].replace(".txt", "")))

def main():
	info = read_metadata("metadata.csv")
	parse_file("oss_export.xml", info)

if __name__ == '__main__':
	main()