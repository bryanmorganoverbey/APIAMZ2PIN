


infile = open('keywords.txt', 'r')
outfile = open('outfile.txt', 'a')
for line in infile:
    words = line.split(' ')
    for word in words:
        word.rstrip('\n')
        outfile.write(word + "\n")
