import cleaviz
import pyqtgraph as pg

def main():
    app = pg.QtGui.QApplication([])
    win = cleaviz.CleavizWindow(sample_rate=10000, segment_length=100)
    win.run()

if __name__ == '__main__':
    main()