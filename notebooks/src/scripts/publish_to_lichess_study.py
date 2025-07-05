from publishers.lichess import LichessPublisher

pub = LichessPublisher()
url = pub.upload_pgn_file("partida_annotated.pgn", study_name="Test de subida")
print("Estudio creado:", url)
