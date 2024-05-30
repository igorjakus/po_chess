from sys import exit
import pygame
import chess

from config import Config
from resource_manager import ResourceManager


class UserInterface:
    def __init__(self, board: chess.Board):
        self.resources = ResourceManager(Config.SQUARE)

        pygame.init()
        self.screen = pygame.display.set_mode(Config.SCREEN_SIZE)
        pygame.display.set_caption("Python Chess - Igor Jakus")
        pygame.display.set_icon(self.resources.logo)

        self.font = pygame.font.SysFont(None, Config.FONT)
        self.small_font = pygame.font.SysFont(None, Config.SMALL_FONT)

        self.board = board
        self.selected_piece = None
        self.flipped_view = False
        self.legal_moves = []
        self.update_screen()

    def reset(self):
        self.board.reset()
        self.selected_piece = None
        self.flipped_view = False
        self.legal_moves = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.__handle_mouse_click()
                self.update_screen()
            elif event.type == pygame.KEYDOWN:
                self.__handle_keydown(event)
                self.update_screen()

    def quit_game(self):
        pygame.quit()
        exit()

    def __handle_keydown(self, event):
        if event.key == pygame.K_SPACE:
            self.flipped_view = not self.flipped_view
        elif event.key == pygame.K_r:
            self.reset()

    def _select_piece(self, square):
        if self.board.color_at(square) is self.board.turn:
            self.selected_piece = square
            self.legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
    
    def player_move(self):
        move_made = False
        while not move_made:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    move_made = self.__handle_mouse_click()
                elif event.type == pygame.KEYDOWN:
                    self.__handle_keydown(event)
                self.update_screen()

    def __handle_mouse_click(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        selected_square = self.__get_square_under_mouse(mouse_x, mouse_y)
        if self.selected_piece is None:
            self._select_piece(selected_square)
        elif selected_square == self.selected_piece:
            self.__deselect_piece()
        else:
            if self.__move_piece(selected_square):
                return True  # move was made
        return False  # move was not made
    def __move_piece(self, square):
        move = chess.Move(self.selected_piece, square)
        if self.__is_promotion(move):
            move.promotion = chess.QUEEN

        if move in self.board.legal_moves:
            self.board.push(move)
            self.selected_piece = None
            self.legal_moves = []
            return True  # move was made
        return False  # move was not made

    def __deselect_piece(self):
        self.selected_piece = None
        self.legal_moves = []

    def __is_promotion(self, move):
        piece = self.board.piece_at(move.from_square)
        return piece and piece.piece_type == chess.PAWN and chess.square_rank(move.to_square) in {0, 7}

    def update_screen(self):
        self.__draw_board()
        self.__draw_effects()
        self.__draw_pieces()
        if self.board.is_game_over():
            self.__draw_game_over()
        pygame.display.flip()

    def __draw_board(self):
        for i in range(8):
            for j in range(8):
                color = Config.BLACK if (i + j) % 2 else Config.WHITE
                rect = (i * Config.SQUARE, j * Config.SQUARE, Config.SQUARE, Config.SQUARE)
                pygame.draw.rect(self.screen, color, rect)

    def __draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                piece_image = self.resources.piece_images[piece.symbol()]
                pos_x, pos_y = self.__square_to_position(square)
                rect = pygame.Rect(pos_x, pos_y, Config.SQUARE, Config.SQUARE)
                self.screen.blit(piece_image, rect)

    def __draw_effects(self):
        self.__highlight_moves()
        self.__highlight_selected()
        self.__highlight_check()

    def __highlight_moves(self):
        for move in self.legal_moves:
            x, y = self.__square_to_position(move.to_square)
            if self.board.is_capture(move):
                rect = (x, y, Config.SQUARE, Config.SQUARE)
                pygame.draw.rect(self.screen, Config.RED, rect)
            else:
                center = (x + Config.SQUARE // 2, y + Config.SQUARE // 2)
                pygame.draw.circle(self.screen, Config.LIGHT_BLUE, center, Config.SQUARE // 7)

    def __highlight_selected(self):
        if self.selected_piece is not None:
            x, y = self.__square_to_position(self.selected_piece)
            rect = (x, y, Config.SQUARE, Config.SQUARE)
            pygame.draw.rect(self.screen, Config.LIGHT_BLUE, rect)

    def __highlight_check(self):
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            x, y = self.__square_to_position(king_square)
            rect = (x, y, Config.SQUARE, Config.SQUARE)
            pygame.draw.rect(self.screen, Config.DARK_RED, rect)

    def __draw_game_over(self):
        text = self.font.render(f"GAME OVER {self.board.result()}", True, Config.DARK_RED)
        text_rect = text.get_rect(center=(Config.SCREEN_SIZE[0] // 2, Config.SCREEN_SIZE[1] // 2))
        self.screen.blit(text, text_rect)

        small_text = self.small_font.render("Press r to start new game", True, Config.DARK_RED)
        small_text_rect = small_text.get_rect(center=(Config.SCREEN_SIZE[0] // 2, Config.SCREEN_SIZE[1] // 2 + Config.SCREEN_SIZE[1] // 15))
        self.screen.blit(small_text, small_text_rect)

    def __get_square_under_mouse(self, mouse_x, mouse_y):
        selected_row = 7 - mouse_y // Config.SQUARE
        selected_col = mouse_x // Config.SQUARE

        if self.flipped_view:
            selected_row = 7 - selected_row
            selected_col = 7 - selected_col

        return chess.square(selected_col, selected_row)

    def __square_to_position(self, square):
        row, col = divmod(square, 8)
        if self.flipped_view:
            col, row = 7 - col, 7 - row

        x = col * Config.SQUARE
        y = (7 - row) * Config.SQUARE
        return x, y

    def flip(self):
        """Flip view so after player move each player see his pieces on the bottom of the board"""
        self.flipped_view = not self.flipped_view