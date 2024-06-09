import chess
from evaluators.piece_tables import PAWN_TABLE, KNIGHT_TABLE, BISHOP_TABLE, ROOK_TABLE
from evaluators.piece_tables import QUEEN_TABLE, KING_MIDGAME_TABLE, KING_ENDGAME_TABLE
from evaluators.evaluator import Evaluator


class AdvancedEvaluator(Evaluator):
    MAX_SCORE = 10_000

    def __init__(self):
        self.cache = dict()

    def evaluate(self, board: chess.Board):
        """Returns evaluation for given board in centipawns"""
        fen = board.board_fen()
        if fen in self.cache:
            return self.cache[fen]

        if board.is_game_over():
            return self.gameover_evaluation(board)

        value = (
            self.material(board) + 
            self.piece_tables(board) +
            self.attacking_squares(board) * 5 +
            self.tempo(board) * 10 +
            self.aggressiveness(board) * 10
        )

        value *= 1 if board.turn == chess.WHITE else -1
        self.cache[fen] = value
        return value

    def gameover_evaluation(self, board):
        winner = board.outcome().winner
        if winner is None:
            return 0  # draw
        if winner == chess.WHITE: 
            return self.MAX_SCORE - len(board.move_stack) # prioritise faster checkmates
        return -self.MAX_SCORE + len(board.move_stack)    # prioritise faster checkmates
    
    def aggressiveness(self, board: chess.Board):
        """Sum of attackers for each square near king"""
        value = 0

        # ile białych figur atakuje czarnego króla i jego otoczenie
        for square in self.get_king_surroundings(board, chess.BLACK):
            value += chess.popcount(board.attackers_mask(chess.WHITE, square))
        
        # ile czarnych figur atakuje białego króla i jego otoczenie
        for square in self.get_king_surroundings(board, chess.WHITE):
            value -= chess.popcount(board.attackers_mask(chess.BLACK, square))
        
        return value

    @staticmethod
    def get_king_surroundings(board: chess.Board, color: chess.Color):
        """Returns list of squares around king"""
        king_square = board.pieces(chess.KING, color).pop()
        
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square) 
        
        surrounding_squares = []
        
        for rank_offset in [-1, 0, 1]:
            for file_offset in [-1, 0, 1]:
                new_rank = king_rank + rank_offset
                new_file = king_file + file_offset
                
                if 0 <= new_rank <= 7 and 0 <= new_file <= 7:  # pole jest na planszy
                    square = chess.square(new_file, new_rank)
                    surrounding_squares.append(square)

        return surrounding_squares

    @staticmethod
    def material(board : chess.Board):
        """Returns material balance in centipawns
        I found it at chessprogramming.com"""
        white = board.occupied_co[chess.WHITE]
        black = board.occupied_co[chess.BLACK]
        return (
            100 * chess.popcount(white & board.pawns) - chess.popcount(black & board.pawns) +
            300 * (chess.popcount(white & board.knights) - chess.popcount(black & board.knights)) +
            300 * (chess.popcount(white & board.bishops) - chess.popcount(black & board.bishops)) +
            500 * (chess.popcount(white & board.rooks) - chess.popcount(black & board.rooks)) +
            900 * (chess.popcount(white & board.queens) - chess.popcount(black & board.queens))
        )

    @staticmethod
    def tempo(board: chess.Board):
        return 1 if board.turn == chess.WHITE else -1

    @staticmethod
    def attacking_squares(board: chess.Board):
        """Count how many squares each side attacks"""
        white_moves = 0
        black_moves = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                attacks_mask = board.attacks_mask(square)
                if piece.color == chess.WHITE:
                    white_moves += chess.popcount(attacks_mask)
                else:
                    black_moves += chess.popcount(attacks_mask)

        return white_moves - black_moves
    
    @staticmethod
    def piece_tables(board: chess.Board) -> int:
        evaluation = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            
            if piece is not None:
                piece_type = piece.piece_type
                color = piece.color
                
                if piece_type == chess.PAWN:
                    table = PAWN_TABLE
                elif piece_type == chess.KNIGHT:
                    table = KNIGHT_TABLE
                elif piece_type == chess.BISHOP:
                    table = BISHOP_TABLE
                elif piece_type == chess.ROOK:
                    table = ROOK_TABLE
                elif piece_type == chess.QUEEN:
                    table = QUEEN_TABLE
                elif piece_type == chess.KING:
                    table = KING_MIDGAME_TABLE
                else:
                    continue
                
                if color == chess.WHITE:
                    evaluation += table[square]
                else:
                    evaluation -= table[chess.square_mirror(square)]
        
        return evaluation