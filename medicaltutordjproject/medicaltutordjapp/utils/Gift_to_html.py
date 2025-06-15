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
    then convert them into HTML form elements.
    """

    def __init__(self, filepath: str): 
        with open(filepath, 'r', encoding='utf-8') as file:
            self.__questions = parser.parseFile(file)
            self.__html = self.__parse()
    
    def questions(self) -> list:
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
                                <input type="checkbox" name="q{q_number}" value="{text}">
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
        html_output.append('</form>')
        
        html_output.append('''<script src="{% static 'js/submitHandler.js' %}"></script>''')
        
        html_output.append('<br><button onclick="showDialog()">Continuar</button>')
        html_output.append('<button onclick="showChatDialog()">Regresar al chat</button>')
        html_output.append("</body>")
        
        return '\n'.join(html_output)

    def identify_gift_question_type(self, gift_question: str) -> str:
        gift_question = gift_question.strip()
    
        match gift_question:
            case q if re.search(r'{\s*(T|F|TRUE|FALSE)\s*}', q, re.IGNORECASE):
                return "True/False"
    
            case q if re.search(r'->', q):
                return "Matching"
    
            case q if re.search(r'{[^}]*~[^}]*=[^}]*}', q):
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
                else:
                    return "Numerical"
    
        return "Unknown"

    def qualify_answers(self, user_answers: dict) -> dict:
        results = {}
        q_number = 0

        if not isinstance(user_answers, dict) or not user_answers:
            raise ValueError("No user answers provided.")

        for question in self.__questions:
            q_number += 1
            source = question.source
            question_type = self.identify_gift_question_type(source)

            if "Numerical" not in question_type:
                standardized_source = re.sub(r'(?<!{)\#.*?(~|})', r'\1', source)
                standardized_source = re.sub(r'(?<!{);.*?(~|})', r'\1', standardized_source)
            else:
                standardized_source = source

            try:
                match question_type:
                    case "True/False":
                        correct_match = re.search(r'{\s*(TRUE|FALSE|T|F)\s*}', standardized_source, re.IGNORECASE)
                        correct_answer = correct_match.group(1).upper() if correct_match else "T"
                        correct_answer = 'T' if correct_answer in ['TRUE', 'T'] else 'F'

                        user_answer = user_answers.get(f"q{q_number}")
                        user_answer = user_answer[0] if isinstance(user_answer, list) else user_answer
                        user_answer = user_answer.strip().upper() if user_answer else ""

                        results[q_number] = {
                            'result': user_answer == correct_answer,
                            'correct_answer': correct_answer,
                            'user_answer': user_answer
                        }

                    case "Multiple Choice (Single Answer)":
                        match_result = re.search(r'{\s*=\s*([^~}]+)', standardized_source)
                        correct_answer = match_result.group(1).strip() if match_result else ""

                        user_answer = user_answers.get(f"q{q_number}")
                        user_answer = user_answer[0] if isinstance(user_answer, list) else user_answer
                        user_answer = user_answer.strip() if user_answer else ""

                        results[q_number] = {
                            'result': user_answer == correct_answer,
                            'correct_answer': correct_answer,
                            'user_answer': user_answer
                        }

                    case "Multiple Choice (Multiple Answers)":
                        answers_with_weights = re.findall(r'~%(-?\d+)%\s*([^~}]+)', standardized_source)
                        correct_answers = {ans.strip(): int(weight) for weight, ans in answers_with_weights if int(weight) > 0}

                        user_selected = user_answers.get(f"q{q_number}", [])
                        if isinstance(user_selected, str):
                            user_selected = [user_selected]

                        user_selected_set = set(a.strip() for a in user_selected)
                        correct_set = set(correct_answers.keys())

                        results[q_number] = {
                            'result': user_selected_set == correct_set,
                            'correct_answer': ', '.join(correct_set),
                            'user_answer': list(user_selected_set)
                        }

                    case "Missing Word":
                        answer_match = re.findall(r'([~=])\s*([^~=}]+)(?=\s*[~=}])', standardized_source)
                        correct_answer = next((ans.strip() for prefix, ans in answer_match if prefix == '='), "Unknown")

                        user_answer = user_answers.get(f"q{q_number}", "")
                        if isinstance(user_answer, list):
                            user_answer = user_answer[0]
                        user_answer = user_answer.strip() if user_answer else ""

                        results[q_number] = {
                            'result': user_answer == correct_answer,
                            'correct_answer': correct_answer,
                            'user_answer': user_answer
                        }

                    case "Matching":
                        pairs = re.findall(r'(\w+)\s*->\s*([\w\s]+)', standardized_source)
                        correct_pairs = {left.strip(): right.strip() for left, right in pairs}
                        user_pairs = {}

                        for idx, key in enumerate(correct_pairs.keys(), start=1):
                            form_key = f"q{q_number}_{idx}"
                            value = user_answers.get(form_key)
                            if value is not None:
                                user_pairs[key] = value.strip()

                        result = user_pairs == correct_pairs
                        formatted_correct = ', '.join([f"{k} -> {v}" for k, v in correct_pairs.items()])

                        results[q_number] = {
                            'result': result,
                            'correct_answer': formatted_correct,
                            'user_answer': [f"{k} -> {v}" for k, v in user_pairs.items()]
                        }

                    case "Short Answer":
                        found_answers = re.findall(r'=\s*([^~}]+)', standardized_source)
                        correct_answers = [ans.strip().lower() for ans in found_answers]
                        user_answer = user_answers.get(f"q{q_number}", "")
                        if isinstance(user_answer, list):
                            user_answer = user_answer[0]
                        user_answer = user_answer.strip().lower() if user_answer else ""

                        results[q_number] = {
                            'result': user_answer in correct_answers,
                            'correct_answer': ', '.join(correct_answers),
                            'user_answer': user_answer
                        }

                    case _ if "Numerical" in question_type:
                        numerical_match = re.search(r'{\s*#\s*([\d.]+)(?:\.\.\s*([\d.]+))?(?::\s*([\d.]+))?\s*}', standardized_source)
                        groups = numerical_match.groups() if numerical_match else (None, None, None)

                        exact_str, range_high_str, margin_str = groups
                        user_answer = user_answers.get(f"q{q_number}", "")
                        if isinstance(user_answer, list):
                            user_answer = user_answer[0].strip()

                        try:
                            if range_high_str:  # Range
                                min_val = float(exact_str)
                                max_val = float(range_high_str)
                                result = min_val <= float(user_answer) <= max_val
                                correct_value = f"{min_val} to {max_val}"
                            else:  # Margin
                                exact = float(exact_str)
                                margin = float(margin_str) if margin_str else 0.0
                                user_val = float(user_answer)
                                result = (exact - margin <= user_val <= exact + margin)
                                correct_value = f"{exact} ± {margin}" if margin > 0 else f"{exact}"
                        except (ValueError, TypeError):
                            result = False
                            correct_value = f"{exact_str} ± {margin_str}" if margin_str else f"{exact_str}"

                        results[q_number] = {
                            'result': result,
                            'correct_answer': correct_value,
                            'user_answer': user_answer
                        }

                    case _:
                        results[q_number] = {
                            'result': False,
                            'correct_answer': 'Unsupported question type',
                            'user_answer': user_answers.get(f"q{q_number}", "")
                        }

            except Exception as e:
                results[q_number] = {
                    'result': False,
                    'correct_answer': f"Error: {str(e)}",
                    'user_answer': user_answers.get(f"q{q_number}", "")
                }

        return results
    
    def get_html(self) -> str:
        return self.__html
        
    def save_file(self, filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(self.__html)



