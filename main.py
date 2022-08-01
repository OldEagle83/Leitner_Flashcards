import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker


main_menu = ['1. Add flashcards', '2. Practice flashcards', '3. Reset stats', '0. Exit']
add_menu = ['1. Add a new flashcard', '2. Exit']
practice_menu = ['press "y" to see the answer:', 'press "n" to skip:', 'press "u" to update:']
update_menu = ['press "d" to delete the flashcard:', 'press "e" to edit the flashcard:']
answer_menu = ['press "y" if your answer is correct:', 'press "n" if your answer is wrong:']
current_q = 'current question: {}'
current_a = 'current answer: {}'
new_q = 'please write a new question:'
new_a = 'please write a new answer:'
msg_wrong_option = '{} is not an option'
msg_question = 'Question: {}'
msg_answer = 'Answer: {}'
msg_q_option = 'Please press "y" to see the answer or press "n" to skip:'
msg_no_cards = 'There is no flashcard to practice!'
msg_exit = 'Bye!'

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# SQLalchemy set up start
Base = declarative_base()


class Flashcards(Base):
    # Child class for declarative_base
    __tablename__ = 'flashcards'

    id = Column(Integer, primary_key=True)
    question = Column(String)
    answer = Column(String)
    box_number = Column(Integer, default=1)


engine = create_engine('sqlite:///flashcard.db?check_same_thread=False', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
query = session.query(Flashcards)


def read_option(input_msg, options=None, failed_msg=None, acceptable=None):
    """
    Function to accept input
    :param input_msg: str: message to display when asking for input
    :param options: list: options to present before asking for input
    :param failed_msg: str: message to display when input is not acceptable
    :param acceptable: list: list of acceptable inputs
    :return: Option (str/int) depends on acceptable list items type
    """
    while True:
        if options:
            print(*options, sep='\n')
        option = input(input_msg)
        if acceptable:
            while True:
                if isinstance(acceptable[0], int):
                    try:
                        option = int(option)
                    except ValueError:
                        pass
                if option in acceptable:
                    return option
                elif failed_msg:
                    print(failed_msg)
                    break
                else:
                    print(msg_wrong_option.format(option))
                    break
        elif option:
            return option


def menu():
    """
    Menu for the flashcards
    1. Add flashcards
    2. Practice flashcards
    3. Exit

    1
    1. Add a new flashcard
    2. Exit
    :return: None
    """
    while True:
        option = read_option('', options=main_menu, acceptable=[1, 2, 3, 0])
        if option == 1:
            while True:
                option = read_option('', options=add_menu, acceptable=[1, 2])
                if option == 1:
                    while True:
                        print(msg_question.format(''))
                        question = input('')
                        if question != ' ' and question:
                            while True:
                                print(msg_answer.format(''))
                                answer = input()
                                if answer != ' ' and answer:
                                    add_card(question, answer)
                                    break
                            break
                if option == 2:
                    break
        elif option == 2:
            logging.debug(query.count())
            if query.count() == 0:
                print(msg_no_cards)
            else:
                play()
        elif option == 3:
            reset_boxes()
        elif option == 0:
            print()
            print(msg_exit)
            return
        print()


def update_card(id):
    """
    Updates a card on the database
    :param id: int: The id of the card
    :return:
    """
    while True:
        card_query = query.filter(Flashcards.id == id)
        for card in card_query:
            print(current_q.format(card.question))
            print(new_q)
            new_question = input()
            if new_question:
                print(current_a.format(card.answer))
                print(new_a)
                new_answer = input()
                if new_answer:
                    card_query.update({'question': new_question, 'answer': new_answer})
                    session.commit()
                    return True

def reset_boxes():
    query.update({'box_number': 1})
    session.commit()


def delete_card(id):
    """
    Deletes a card from the database
    :param id: int: id of the card
    :return: bool
    """
    try:
        card_query = query.filter(Flashcards.id == id)
        card_query.delete()
        session.commit()
        return True
    except:
        return False


def add_card(question, answer):
    """
    Adds a card to the database
    :param question: str: Question
    :param answer: str: Answer
    :return: bool
    """
    try:
        new_question = Flashcards(question=question, answer=answer)
        session.add(new_question)
        session.commit()
        return True
    except:
        return False


def move_card(id, direction):
    """
    Moves the card to another box, according to direction. Cards move to the first box when moving to the left (minus)
    Cards move one box at a time when moving to the right (positive) 0. 1 -> 2 -> 3
    When direction = 0, the card is moved to box 0 and you won't be asked about this card.
    :param id: int: id of the card
    :param direction: int: 0, 1, -1 depending on where you want the card to go.
    :return: bool
    """
    try:
        card_query = query.filter(Flashcards.id == id)
        if direction == -1:
            card_query.update({'box_number': 1})
        elif direction == 1 and card_query[0].box_number < 3:
            card_query.update({'box_number': card_query[0].box_number + 1})
        else:
            card_query.update({'box_number': 0})
        session.commit()
        return True
    except:
        return False


def play():
    """
    Will ask questions by their membership in a box: 1, 2, 3
    If a question is answered correctly it will be moved one box to the right (ex: 2 -> 3)
    If a question is answered correctly and it was in box 3, it will be deleted.
    If a question is answered incorrectly it will be moved in box 1
    :return: None
    """
    questions_dict = dict()
    for i in range(1, 4):
        questions_dict[i] = session.query(Flashcards).filter(Flashcards.box_number == i)
    if len(questions_dict.values()) == 0:
        print(msg_no_cards)
        return
    for j, questions in questions_dict.items():
        for question in questions:
            logging.debug(f'Working with question id: {question.id}')
            print(msg_question.format(question.question))
            selection = read_option('', options=practice_menu, acceptable=['y', 'n', 'u'])
            if selection == 'y':
                print(msg_answer.format(question.answer))
                selection = read_option('', options=answer_menu, acceptable=['y', 'n'])
                if selection == 'n':
                    move_card(question.id, -1)
                elif selection == 'y':
                    move_card(question.id, 1)
            elif selection == 'n':
                continue
            else:
                selection = read_option('', options=update_menu, acceptable=['d', 'e'])
                if selection == 'd':
                    delete_card(question.id)
                elif selection == 'e':
                    update_card(question.id)
    return


if __name__ == '__main__':
    menu()
