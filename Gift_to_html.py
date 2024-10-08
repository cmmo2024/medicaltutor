# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 20:31:49 2024

@author: Alejandro
"""

from pygiftparser import parser

import re

class gisfttohtml(object):
    
    """
    The gisfttohtml class is designed to read and parse questions written in GIFT format,
    then convert them into HTML form elements. This class provides methods for loading
    questions from a file, identifying question types, converting them into HTML, 
    and saving the HTML output to a file.

    Attributes:
    -----------
    __questions : list
        A list of questions parsed from the GIFT file.
    
    __html : str
        The HTML output generated from the parsed questions, containing form elements 
        for each question.

    Methods:
    --------
    __init__(filepath: str):
        Initializes the class by loading a GIFT file, parsing its questions, and generating HTML.

    questions():
        Returns the list of parsed questions from the GIFT file.

    __parse():
        Converts the parsed GIFT questions into HTML format and returns the HTML string.

    identify_gift_question_type(gift_question: str):
        Identifies and returns the type of a question from a GIFT format string.

    get_html():
        Returns the generated HTML string.

    save_file(filepath: str):
        Saves the generated HTML output to a specified file.
    """

    def __init__(self, filepath: str): 
        
        """
        Initializes the gisfttohtml class by reading a GIFT format file, parsing its contents,
        and generating an HTML output for the questions.
        
        :param filepath: Path to the GIFT format file.
        :type filepath: str
        
        The method reads the file content, parses the questions using a GIFT parser, 
        and stores the parsed questions in `self.__questions`. 
        It also calls `self.__parse()` to convert the parsed questions into HTML format 
        and stores the resulting HTML in `self.__html`.
        """
        
        with open(filepath, 'r', encoding='utf-8') as file:
            
            self.__questions=parser.parseFile(file)
            
            self.__html=self.__parse()
    
    def questions(self) -> list:
        
        """
        Returns the list of parsed questions.
    
        :return: A list of questions parsed from the GIFT format file.
        :rtype: list
    
        This method allows access to the questions that were parsed during initialization.
        """
        
        return self.__questions
    
    def __parse(self) -> str:
        
        """
        Converts the parsed GIFT questions into HTML format.
    
        :return: The generated HTML output as a string.
        :rtype: str
    
        This method iterates over each parsed question and generates the corresponding HTML form elements 
        based on the question type (e.g., True/False, Multiple Choice, Matching, etc.). 
        It appends the generated HTML for each question to a list, which is then joined and returned 
        as a single HTML output.
        """
        
        html_output = []
        
        for q in self.__questions:
            
            question_id = q.id
            question_text = q.text
            source = q.source
            question_type = self.identify_gift_question_type(source)
            
            if "Numerical" not in question_type and question_type != "True/False":
                answers = q.answers.answers
            
            html_output.append(f'<h3>{question_text}</h3>')
            html_output.append('<form>')
            
            match question_type:
                
                case "True/False":
                    true = 'V'
                    false = 'F'
                    
                    html_output.append(f'''
                        <label>
                            <input type="radio" name="q{question_id}" value="{true}">
                            {true}
                        </label><br>
                        <label>
                            <input type="radio" name="q{question_id}" value="{false}">
                            {false}
                        </label><br>
                    ''')
    
                case "Missing Word":
                    answer_block = re.search(r'{([^}]+)}', source)
                    
                    if answer_block:
                        
                        answer_text = answer_block.group(1)
                        answer_options = re.split(r'[~=]', answer_text)
                        
                        dropdown_html = f'<select name="q{question_id}"><option value="" disabled selected>Select an answer</option>'
                        
                        for answer in answer_options:
                            clean_answer = answer.strip()  
                            if clean_answer:
                                dropdown_html += f'<option value="{clean_answer}">{clean_answer}</option>'
                        
                        dropdown_html += '</select>'
                        
                        modified_question_text = re.sub(r'{[^}]+}', dropdown_html, source)
                        html_output.append(f'<p>{modified_question_text}</p>')
    
                case "Multiple Choice (Multiple Answers)":
                    for answer in answers:
                        text = answer.answer
                        
                        html_output.append(f'''
                            <label>
                                <input type="checkbox" id="myCheck">
                                {text}
                            </label><br>
                        ''')
    
                case "Multiple Choice (Single Answer)":
                    for answer in answers:
                        text = answer.answer
                        
                        html_output.append(f'''
                            <label>
                                <input type="radio" name="q{question_id}" value="{text}">
                                {text}
                            </label><br>
                        ''')
    
                case "Matching":
                    html_template = ""
                    pairs = []
                    
                    for answer in answers:
                        pairs.append((answer.question, answer.answer))
                    
                    for question, _ in pairs:
                        html_template += f"""
                        <div style="margin-bottom: 10px;">
                            <label style="display: inline-block; width: 150px;">{question}</label>
                            <select style="display: inline-block; padding: 5px;">
                                <option value="" disabled selected>Select an answer</option>"""
                    
                        for _, answer in pairs:
                            html_template += f"<option value='{answer}'>{answer}</option>"
                    
                        html_template += """
                            </select>
                        </div>"""
                    
                    html_output.append(html_template)
    
                case "Short Answer":
                    html_output.append('''<input type="text" onfocus="this.value=''" value=""><br>''')
                    
                case _ if "Numerical" in question_type:
                    html_output.append('''<input type="text" onfocus="this.value=''" value=""><br>''')
            
            html_output.append('''<br><input type="submit" value="Submit">''')
            html_output.append('</form>')
        
        return '\n'.join(html_output)
    
    def identify_gift_question_type(self, gift_question: str) -> str:
        
        """
        Identifies the type of question from a GIFT format string.
    
        :param gift_question: A question in GIFT format.
        :type gift_question: str
    
        :return: The type of the question (e.g., True/False, Multiple Choice, Short Answer, Matching).
        :rtype: str
    
        This method uses regular expressions to determine the type of question 
        (e.g., True/False, Multiple Choice, etc.). It matches specific patterns 
        in the GIFT format and returns the corresponding question type as a string.
        """
        
        gift_question = gift_question.strip()
    
        match gift_question:
            case q if re.search(r'{\s*(T|F|TRUE|FALSE)\s*}', q, re.IGNORECASE):
                return "True/False"
    
            case q if re.search(r'->', q):
                return "Matching"
    
            case q if re.search(r'.*{[^}]*~[^}]*=[^}]*~[^}]*}.*', q):
                return "Missing Word"
    
            case q if re.search(r'{=[^~]*}', q):
                return "Short Answer"
    
            case q if re.search(r'{[^}]*~%[0-9]+%[^}]*~%[0-9]+%[^}]*}', q):
                return "Multiple Choice (Multiple Answers)"
    
            case q if re.search(r'{[^#][^}]*[=~][^}]*}', q):
                return "Multiple Choice (Single Answer)"
    
            case q if re.search(r'{\s*#', q):
                if re.search(r'{\s*#\d+(\.\d+)?\s*:\s*\d+(\.\d+)?\s*}', q):
                    return "Numerical (with error margin)"
                elif re.search(r'{\s*#\d+(\.\d+)?\s*\.\.\s*\d+(\.\d+)?\s*}', q):
                    return "Numerical (range)"
                elif re.search(r'{\s*#\s*=[^}]*}', q):
                    return "Numerical (multiple answers)"
                else:
                    return "Numerical"
    
        return "Unknown"
    
    def get_html(self) -> str:
        
        """
        Returns the generated HTML output.
    
        :return: The HTML output for the parsed questions.
        :rtype: str
    
        This method provides access to the HTML generated by the `__parse` method.
        It returns the HTML string that contains the form elements for all questions.
        """
        
        return self.__html
        
    def save_file(self, filepath: str) -> None: 
        
        """
        Saves the generated HTML output to a specified file.
    
        :param filepath: The path where the HTML file will be saved.
        :type filepath: str
    
        This method writes the HTML output generated by `__parse()` into a file
        located at the specified `filepath`.
        """
        
        with open(filepath, 'w', encoding='utf-8') as file: 
            file.write(self.__html)
        







