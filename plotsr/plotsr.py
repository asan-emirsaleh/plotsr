#!/usr/bin/env python3

import argparse


"""
Annotation BED file format:

Chromosome ID
0-based start
1-based end
Genome (R/Q)
Marker (As defined here: https://matplotlib.org/stable/api/markers_api.html)
Marker colour (Name or hexadecimal)
Marker size
Annotations text
Annotations text color (Name or hexadecimal)
Annotations text size
"""


if __name__ == '__main__':
    from matplotlib.rcsetup import non_interactive_bk as bklist
    parser = argparse.ArgumentParser("Arguments for plotting SRs predicted by SyRI",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(dest='reg', help='syri.out file generated by SyRI', type=argparse.FileType('r'))
    parser.add_argument(dest='r', help='path to reference genome', type=argparse.FileType('r'))
    parser.add_argument(dest='q', help='path to query genome', type=argparse.FileType('r'))
    parser.add_argument('-B', help='Annotation bed file for marking specific positions on genome', type=argparse.FileType('r'))
    parser.add_argument('--chr', help='Select reference chromosomes to be plotted. By default: all chromosomes are printed.', type=str, nargs='+')
    parser.add_argument('--nosyn', help='Do not plot syntenic regions', default=False, action='store_true')
    parser.add_argument('--noinv', help='Do not plot inversions', default=False, action='store_true')
    parser.add_argument('--notr', help='Do not plot translocations regions', default=False, action='store_true')
    parser.add_argument('--nodup', help='Do not plot duplications regions', default=False, action='store_true')
    parser.add_argument('-s', help='minimum size of a SR to be plotted', type=int, default=10000)
    parser.add_argument('-R', help='Create ribbons', default=False, action="store_true")
    parser.add_argument('-f', help='font size', type=int, default=6)
    parser.add_argument('-H', help='height of the plot', type=int)
    parser.add_argument('-W', help='width of the plot', type=int)
    parser.add_argument('-S', help='Space between homologous chromosome (0.1-0.9). Adjust this to make more space for annotation marker/text.', default=0.7, type=float)
    parser.add_argument('-o', help='output file format (pdf, png, svg)', default="pdf", choices=['pdf', 'png', 'svg'])
    parser.add_argument('-d', help='DPI for the final image', default="300", type=int)
    parser.add_argument('-b', help='Matplotlib backend to use', default="agg", type=str, choices=bklist)
    parser.add_argument('-v', help='Plot vertical chromosome', default=False, action='store_true')
    parser.add_argument('--log', help='Log-level', choices=['DEBUG', 'INFO', 'WARN'], default='WARN', type=str)


    args = parser.parse_args([])
    args = parser.parse_args()

    import logging
    import logging.config

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'log_file': {
                'format': "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            },
            'stdout': {
                'format': "%(name)s - %(levelname)s - %(message)s",
            },
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'formatter': 'stdout',
                'level': 'WARNING',
            },
            # 'log_file': {
            #     'class': 'logging.FileHandler',
            #     'filename': args.log_fin.name,
            #     'mode': 'a',
            #     'formatter': 'log_file',
            #     'level': args.log,
            # },
        },
        'loggers': {
            '': {
                'level': args.log,
                'handlers': ['stdout'],
                # 'handlers': ['stdout', 'log_file'],
            },
        },
    })

    logger = logging.getLogger("Plotsr")


    # CONSTANTS
    VARS = ['SYN', 'INV', 'TRANS', 'INVTR', 'DUP', 'INVDP']
    COLORS = ['#DEDEDE', '#FFA500', '#9ACD32', '#9ACD32', '#00BBFF', '#00BBFF', '#83AAFF', '#FF6A33']

    # Set Figure height and width. Change later based on chromosome number and size
    FS = args.f             # Font size
    H = args.H              # Height
    W = args.W              # Width
    O = args.o              # Output file format
    D = args.d              # Output file DPI
    R = args.R              # Create ribbons
    V = args.v              # Vertical chromosomes
    S = args.S              # Space between homologous chromosomes
    B = None if args.B is None else args.B.name              # Annotation bed file

    if S < 0.1 or S > 0.9:
        sys.exit('Out of range value for S. Please provide a value in the range 0.1-0.9')

    from plotsr.plotsr_func import VARS, readfasta
    from collections import deque

    fins = ['col_lersyri.out', 'ler_cvisyri.out', 'cvi_colsyri.out']
    # Read alignment coords
    alignments = deque()
    chrids = deque()
    if syriout: # TODO: write proper check
        for fin in fins:    ## TODO: define proper fins
            al, cid = readsyriout(fin)
            alignments.append([os.path.basename(fin), al])
            chrids.append((os.path.basename(fin), cid))
    elif bedout: # TODO: write proper check
        for fin in fins: # TODO: define proper fins
            al, cid = readbedout(fin)
            alignments.append([os.path.basename(fin), al])
            chrids.append((os.path.basename(fin), cid))

    # Check chromsome IDs and sizes
    chrlengths = validalign2fasta(alignments, args.genomes) # TODO: define args.genomes
    chrlengths = validalign2fasta(alignments, 'genomes.txt') # TODO: define args.genomes

    # Filter alignments to select long alignments between homologous chromosomes
    for i in range(len(alignments)):
        alignments[i][1] = filterinput(args, alignments[i][1], chrids[i][1])

    # Select only chromosomes selected by --chr
    if args.chr is not None:
        # TODO: IMPLEMENT selectchrs
        pass

    # Combine Ribbon is selected than combine rows
    if R:
        for i in range(len(alignments)):
            alignments[i][1] = createribbon(alignments[i][1])

    # invert coord for inverted query genome

    for i in range(len(alignments)):
        df = alignments[i][1].copy()
        invindex = ['INV' in i for i in df['type']]
        df.loc[invindex, 'bstart'] = df.loc[invindex, 'bstart'] + df.loc[invindex, 'bend']
        df.loc[invindex, 'bend'] = df.loc[invindex, 'bstart'] - df.loc[invindex, 'bend']
        df.loc[invindex, 'bstart'] = df.loc[invindex, 'bstart'] - df.loc[invindex, 'bend']
        alignments[i][1] = df.copy()

    chrs = [k for k in chrids[0][1].keys() if k in alignments[0][1]['achr'].unique()] # TODO: SEE WHAT TO DO WITH THIS
    # Get groups of homologous chromosomes
    chrgrps = {}
    for c in chrs:
        cg = deque([c])
        cur = c
        for i in range(len(chrids)):
            n = chrids[i][1][cur]
            cg.append(n)
            cur = n
        chrgrps[c] = cg

    import matplotlib
    try:
        # matplotlib.use(args.b)
        matplotlib.use('Qt5Agg')
    except:
        sys.exit('Matplotlib backend cannot be selected')
    from matplotlib import pyplot as plt

    plt.rcParams['font.size'] = FS
    try:
        if H is None and W is None:
            H = len(chrs)
            W = 3
            fig = plt.figure(figsize=[W, H])
        if H is not None and W is None:
            fig = plt.figure(figsize=[H, H])
        if H is None and W is not None:
            fig = plt.figure(figsize=[W, W])
        if H is not None and W is not None:
            fig = plt.figure(figsize=[W, H])
    except Exception as e:
        sys.exit("Error in initiliazing figure. Try using a different backend." + '\n' + e.with_traceback())
    ax = fig.add_subplot(111, frameon=False)

    ## Draw Axes
    ax, max_l = drawax(ax, chrgrps, chrlengths, V, S)

    ## Draw Chromosomes
    # TODO: Set parsing of colors
    ax, indents = pltchrom(ax, chrs, chrgrps, chrlengths, V, S)

    # Plot structural annotations
    # TODO: Parameterise: colors, alpha,
    ax = pltsv(ax, alignments, chrs, V, chrgrps, indents)

    # Draw legend
    # TODO: Consider grouping the chromosomes legends at one place
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.01, 1, 1.01), ncol=3, mode='expand', borderaxespad=0., frameon=False)

    # Plot markers
    if B is not None:
        mdata = readannobed(B, V, chrlengths)
        for m in mdata:
            ind = [i for i in range(len(chrlengths)) if chrlengths[i][0] == m.genome][0]
            indent = indents[ind]
            offset = chrs.index([k for k, v in chrgrps.items() if v[ind] == m.chr][0])
            if not V:
                ax.plot(m.start, indent-offset, marker=m.mtype, color=m.mcol, markersize=m.msize)
                if m.text != '':
                    ax.text(m.start, indent-offset+m.tpos, m.text, color=m.tcol, fontsize=m.tsize, fontfamily=m.tfont, ha='center', va='bottom')

            elif V:
                ax.plot(indent+offset, m.start, marker=m.mtype, color=m.mcol, markersize=m.msize)
                if m.text != '':
                    ax.text(indent+offset-m.tpos, m.start, m.text, color=m.tcol, fontsize=m.tsize, fontfamily=m.tfont, ha='left', va='center', rotation='vertical')

    # Save the plot
    try:
        fig.savefig('syri.'+O, dpi=D, bbox_inches='tight', pad_inches=0.01)
    except Exception as e:
        sys.exit('Error in saving the figure. Try using a different backend.' + '\n' + e.with_traceback())
