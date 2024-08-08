
import config


lines_seen = set() # holds lines already seen
lines_cut = set()
outfile = open(config.file_desconhecido_filtrado, "w")
for line in open(config.file_produto_desconhecido, "r"):
        lines_cut.add(line[21:])


for line in lines_cut:
    if line not in lines_seen: # not a duplicate
        outfile.write(line)
        lines_seen.add(line)
outfile.close()

print('done')