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
        
        html_output = ["<!DOCTYPE html>", '''<html lang="es">''']
        
        html_output.append('''<head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Cuestionario</title>
                            {% load static %}
                            <link rel="stylesheet" href="{% static 'css/common.css' %}"
                            <link rel="stylesheet" href="{% static 'css/questions.css' %}">
                        </head>''')
        
        html_output.append('<body>')
        html_output.append('''<form id="questions-form" action="/qualify_answers/" method="POST">''')
        #html_output.append('''<form id="questions-form" action="{% url 'qualified_answers' %}" method="POST">''')
        html_output.append("{% csrf_token %}")
        
        q_number = 0
        
        for q in self.__questions:
            q_number += 1
            question_text = q.text
            source = q.source
            question_type = self.identify_gift_question_type(source)
            
            if "Numerical" not in question_type and question_type != "True/False":
                answers = q.answers.answers
    
            html_output.append(f'<h3>{question_text}</h3>')
            
            match question_type:
                case "True/False":
                    html_output.append(f'''
                        <label>
                            <input type="radio" name="q{q_number}" value="T">
                            V
                        </label><br>
                        <label>
                            <input type="radio" name="q{q_number}" value="F">
                            F
                        </label><br>
                    ''')
    
                case "Missing Word":
                    answer_block = re.search(r'{([^}]+)}', source)
                    if answer_block:
                        answer_text = answer_block.group(1)
                        answer_options = re.split(r'[~=]', answer_text)
                        dropdown_html = f'<select name="q{q_number}"><option value="" disabled selected>Select an answer</option>'
                        
                        for answer in answer_options:
                            clean_answer = answer.strip()
                            if clean_answer:
                                dropdown_html += f'<option value="{clean_answer}">{clean_answer}</option>'
                        
                        dropdown_html += '</select>'
                        modified_question_text = re.sub(r'{[^}]+}', dropdown_html, source)
                        html_output.append(f'<p>{modified_question_text}</p>')
    
                case "Multiple Choice (Single Answer)":
                    for answer in answers:
                        text = answer.answer
                        html_output.append(f'''
                            <label>
                                <input type="radio" name="q{q_number}" value="{text}">
                                {text}
                            </label><br>
                        ''')
    
                case "Multiple Choice (Multiple Answers)":
                    idx = 1
                    for answer in answers:
                        text = answer.answer
                        html_output.append(f'''
                            <label>
                                <input type="checkbox" name="q{q_number}_{idx}" value="{text}">
                                {text}
                            </label><br>
                        ''')
                        idx += 1
    
                case "Matching":
                    pairs = [(answer.question, answer.answer) for answer in answers]
                    for idx, (question_part, _) in enumerate(pairs, start=1):
                        html_output.append(f'''
                        <div style="margin-bottom: 10px;">
                            <label style="display: inline-block; width: 150px;">{question_part}</label>
                            <select name="q{q_number}_{idx}" style="display: inline-block; padding: 5px;">
                                <option value="" disabled selected>Select an answer</option>''')
                        
                        for _, answer in pairs:
                            html_output.append(f"<option value='{answer}'>{answer}</option>")
                        
                        html_output.append("""
                            </select>
                        </div>""")
    
                case "Short Answer":
                    html_output.append(f'<input type="text" name="q{q_number}" value=""><br>')
                
                case _ if "Numerical" in question_type:
                    html_output.append(f'<input type="text" name="q{q_number}" value=""><br>')
    
        html_output.append('''<!-- Modal Dialog -->
        <div id="confirmation-dialog" class="modal">
            <div class="modal-content">
                <p>¿Seguro que quieres continuar? No podrás realizar cambios en este formulario una vez calificado ¡Revisa bien!</p>
                <input type="submit" value="Calificar">
                <button onclick="closeDialog()" type="button">Seguir revisando</button>
            </div>
        </div>
        <!-- Modal Dialog for "Regresar al chat" -->
        <div id="chat-confirmation-dialog" class="modal">
            <div class="modal-content">
                <p>¿Seguro que quieres regresar al chat? Perderás el progreso en este cuestionario.</p>
                <button id="confirm-go-home-button" type="button">Regresar al chat</button>
                <button onclick="closeDialog()" type="button">Seguir revisando</button>
            </div>
        </div>
        <div id="overlay" class="modal-overlay"></div>''')
        # Add a single submit button for the entire form
        html_output.append('</form>')
        
        html_output.append('''<script src="{% static 'js/submitHandler.js' %}"></script>''')
        
        html_output.append('<br><button onclick="showDialog()">Continuar</button>')
        html_output.append('<button onclick="showChatDialog()">Regresar al chat</button>')
        html_output.append("</body>")
        
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
    
            # Updated Missing Word regex: looks for both `=` and at least one `~` inside `{...}`
            case q if re.search(r'{[^}]*~[^}]*=[^}]*}', q):
                return "Missing Word"
    
            # Short Answer: A single answer with `=` and no `~`
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
                else:
                    return "Numerical"
    
        return "Unknown"

    def qualify_answers(self, user_answers: dict) -> dict:
        results = {}
        q_number = 0  # Main question identifier
    
        for question in self.__questions:
            q_number += 1
            source = question.source
            question_type = self.identify_gift_question_type(source)
    
            if "Numerical" not in question_type:
                standardized_source = re.sub(r'(?<!{)\#.*?(~|})', r'\1', source)
                standardized_source = re.sub(r'(?<!{);.*?(~|})', r'\1', standardized_source)
            else:
                standardized_source = source
    
            match question_type:
                case "True/False":
                    correct_answer_match = re.search(r'{\s*(TRUE|FALSE|T|F)\s*}', standardized_source, re.IGNORECASE)
                    if correct_answer_match:
                        correct_answer = correct_answer_match.group(1).upper()
                        if correct_answer == 'TRUE':
                            correct_answer = 'T'
                        elif correct_answer == 'FALSE':
                            correct_answer = 'F'
                        user_answer = user_answers.get(f"q{q_number}")
                        if isinstance(user_answer, list):
                            user_answer = user_answer[0]  # If multiple answers, take the first one
                        user_answer = user_answer.strip().upper() if user_answer else ""
                        result = (user_answer == correct_answer)
                        results[q_number] = {
                            'result': result,
                            'correct_answer': correct_answer
                        }
    
                case "Multiple Choice (Single Answer)":
                    correct_answer = re.search(r'{\s*=\s*([^~}]+)', standardized_source)
                    if correct_answer:
                        correct_answer = correct_answer.group(1).strip()
                        user_answer = user_answers.get(f"q{q_number}")
                        if isinstance(user_answer, list):
                            user_answer = user_answer[0].strip()  # Take the first answer if multiple given
                        else:
                            user_answer = user_answer.strip() if user_answer else ""
                        results[q_number] = {
                            'result': (user_answer == correct_answer),
                            'correct_answer': correct_answer
                        }
    
                case "Multiple Choice (Multiple Answers)":
                    answers_with_weights = re.findall(r'~%(-?\d+)%\s*([^~}]+)', standardized_source)
                    correct_answers = {answer.strip(): int(weight) for weight, answer in answers_with_weights}
    
                    # Collect user-selected answers from `user_answers[q_number]` as a set
                    user_selected_answers = set(map(str.strip, user_answers.get(f"q{q_number}", [])))
    
                    # Correct answers that contribute positively
                    correct_set = {answer.strip() for answer, weight in correct_answers.items() if weight > 0}
                    result = (user_selected_answers == correct_set)
    
                    formatted_correct_answers = ', '.join(correct_set)
                    results[q_number] = {
                        'result': result,
                        'correct_answer': formatted_correct_answers
                    }

                case "Missing Word":
                    answer_match = re.findall(r'([~=])\s*([^~=}]+)(?=\s*[~=}])', standardized_source)
                    correct_answer = next((answer.strip() for prefix, answer in answer_match if prefix == '='), None)
                    user_answer = user_answers.get(f"q{q_number}", "")
                    if isinstance(user_answer, list):
                        user_answer = user_answer[0].strip()  # Take the first answer if multiple were given
                    else:
                        user_answer = user_answer.strip()
                    result = (user_answer == correct_answer)
                    results[q_number] = {
                        'result': result,
                        'correct_answer': correct_answer if correct_answer else "Unknown"
                    }
    
                case "Matching":
                    pairs = re.findall(r'(\w+)\s*->\s*([\w\s]+)', standardized_source)
                    correct_pairs = {pair[0].strip(): pair[1].strip() for pair in pairs}
                    
                    # Get the user answers from `user_answers[q_number]` as a list of answers
                    user_answers_list = user_answers.get(f"q{q_number}", [])
                    
                    # Match each user answer to its corresponding correct pair
                    user_pairs = {list(correct_pairs.keys())[i]: user_answers_list[i].strip()
                                  for i in range(len(user_answers_list))}
    
                    # Compare dictionaries to determine if all pairs are correct
                    result = user_pairs == correct_pairs
                    formatted_correct_pairs = ', '.join([f"{k} -> {v}" for k, v in correct_pairs.items()])
                    results[q_number] = {
                        'result': result,
                        'correct_answer': formatted_correct_pairs
                    }
    
                case "Short Answer":
                    correct_answers = str(re.findall(r'=\s*([^~}]+)', standardized_source))[2:-2].split('=')
                    formatted_correct_answers = ', '.join(correct_answers)
                    correct_answers = [ans.strip().lower() for ans in correct_answers]
                    user_answer = user_answers.get(f"q{q_number}", "").strip().lower()
                    if isinstance(user_answer, list):
                        user_answer = user_answer[0].strip().lower()  # Use the first if multiple
                    result = user_answer in correct_answers
                    results[q_number] = {
                        'result': result,
                        'correct_answer': formatted_correct_answers
                    }
    
                case _ if "Numerical" in question_type:
                    numerical_answer = re.search(r'{\s*#\s*([\d.]+)(?:\.\.\s*([\d.]+))?(?::\s*([\d.]+))?\s*}', standardized_source)
                    groups = numerical_answer.groups() if numerical_answer else (None, None, None)
    
                    if groups[0] and '..' in groups[0]:
                        temp = groups[0].split('..')
                        groups = (temp[0], temp[1], None)
    
                    if numerical_answer:
                        exact_str, range_high_str, margin_str = groups
                        user_answer = user_answers.get(f"q{q_number}")
                        if isinstance(user_answer, list):
                            user_answer = user_answer[0].strip()
    
                        try:
                            if range_high_str:
                                min_val = float(exact_str)
                                max_val = float(range_high_str)
                                result = min_val <= float(user_answer) <= max_val
                                results[q_number] = {
                                    'result': result,
                                    'correct_answer': f"{min_val} to {max_val}"
                                }
                            else:
                                exact = float(exact_str)
                                margin = float(margin_str) if margin_str else 0.0
                                user_value = float(user_answer)
                                result = (exact - margin <= user_value < exact + margin)
                                results[q_number] = {
                                    'result': result,
                                    'correct_answer': f"{exact} ± {margin}" if margin > 0 else f"{exact}"
                                }
                        except (TypeError, ValueError):
                            results[q_number] = {
                                'result': False,
                                'correct_answer': f"{exact_str} ± {margin_str}" if margin_str else f"{exact_str}"
                            }
    
        return results
    
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
        







