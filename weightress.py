import numpy as np
import scipy.sparse.linalg as la
import bs4
from scipy import sparse

def get_text_elements(elem):
    if isinstance(elem, bs4.NavigableString):
        if type(elem) not in (bs4.Comment, bs4.Declaration) and elem.strip():
            yield elem
    elif elem.name not in ('script', 'style'):
        for content in elem.contents:
            for text_elem in get_text_elements(content):
                yield text_elem

class SSPageRank(object):
    def __init__(self, alpha=0.1, beta=1.0):
        self.alpha = alpha
        self.beta = beta

    def fit(self, A, u):
        n = A.shape[0]
        D = sparse.diags(np.asarray(A.sum(axis=1).T), [0])
        L = D - A
        self.f = la.spsolve(L+self.alpha*sparse.identity(n), u)
        #self.f = la.spsolve(self.beta*L/(n**2)+self.alpha*sparse.identity(n), u) # <- this is the correct formula,
        self.f = la.spsolve(self.beta*L+self.alpha*sparse.identity(n), u) # but we use this one for convenience
        self.f = np.maximum(0.0, self.f)
        return self

class DomPageRank(SSPageRank):
    def weight_func(self):
        """
        Weight function to DOM elements
        default: text uniform weight
        You can implement your own weight function by overriding this function
        """
        # text uniform weight (default)
        u = np.zeros(self.n_elems)
        mask = np.array([elem.id for elem in get_text_elements(self.soup.body)])
        u[mask] = 1.0
        return u

    def fit(self, html):
        self.soup = bs4.BeautifulSoup(html, "lxml")

        # assign an id to each element
        setattr(self.soup, "id", 0)
        self.elems = []
        for elem_id, elem in enumerate(self.soup.descendants, start=1):
            setattr(elem, "id", elem_id)
            self.elems.append(elem)
        self.elems = [self.soup.body] + self.elems
        self.n_elems = len(self.elems)

        # create undirected adjacency matrix
        A = sparse.lil_matrix((self.n_elems, self.n_elems))
        for elem in self.elems:
            i = elem.id
            j = elem.parent.id
            A[i,j] = 1
            if not hasattr(elem, "children"):
                continue
            for child in elem.children:
                j = child.id
                A[j,i] = 1
        A = A + A.T

        # compute initial weight. default: text_uniform_weight
        u = self.weight_func()
        super(DomPageRank, self).fit(A, u)
        return self

class ContentExtractor(DomPageRank):
    tags = set(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'table', 'map', 'section', 'article', 'ul'])
    irrelevant_tags = set(['script', 'style', 'nav', 'aside'])

    def weight_func(self):
        def get_text_elements(elem):
            if isinstance(elem, bs4.NavigableString):
                if type(elem) not in (bs4.Comment, bs4.Declaration) and elem.strip():
                    yield elem
            elif elem.name not in ContentExtractor.irrelevant_tags:
                for content in elem.contents:
                    for text_elem in get_text_elements(content):
                        yield text_elem
        u = np.zeros(self.n_elems)
        elems = [elem for elem in get_text_elements(self.soup.body)]
        for elem in elems:
            u[elem.id] = len(elem.string.strip())
        return u

    def get_weighted_texts(self, root=None):
        root = root if root is not None else self.soup.body
        if not hasattr(self, "g"):
            self.weight_elements(root)
        h = []
        def extract(elem, weight):
            if isinstance(elem, bs4.NavigableString):
                if type(elem) not in (bs4.Comment, bs4.Declaration) and elem.strip():
                    h.append((elem.string.strip(), weight))
            elif elem.name not in ContentExtractor.irrelevant_tags:
                for content in elem.contents:
                    if elem.id in self.g:
                        extract(content, weight + self.g[elem.id])
                    else:
                        extract(content, weight)
        extract(root, 0.0)
        return h

    def weight_elements(self, root=None):
        root = root if root is not None else self.soup.body
        elems = [root] + list(root.descendants)
        self.g = {}
        for elem in elems:
            if elem.name not in ContentExtractor.tags:
                continue
            score = self.f[elem.id]
            if hasattr(elem, "children"):
                for child in elem.children:
                    if child.name in ContentExtractor.tags:
                        score += self.f[child.id]
            self.g.setdefault(elem.id, score)

    def extract_elements(self, root=None, topn=1):
        root = root if root is not None else self.soup.body
        if not hasattr(self, "g"):
            self.weight_elements(root)
        elems = [elem for elem in [root] + list(root.descendants) if elem.id in self.g]
        scores = [self.g[elem.id] for elem in elems]
        return [(elems[i], scores[i]) for i in np.argsort(scores)[::-1][:topn]]

    def extract_text(self, deliminator=u" "):
        elem, score = self.extract_elements(topn=1)[0]
        self.text = deliminator.join(elem.string.strip() for elem in get_text_elements(elem) if elem.string.strip())
        return self.text

    def extract_images(self, topn=1):
        image_scores = []
        for elem, score in self.extract_elements(topn=topn):
            for image in elem.find_all("img"):
                image_scores.append((image.attrs["src"], score))
        return image_scores

if __name__ == '__main__':
    import os, sys, codecs, hashlib, requests
    def url_open(url, loc="/tmp", encoding=None):
        filename = hashlib.md5(url).hexdigest() + ".html"
        filename = os.path.join(loc, filename)
        if os.path.exists(filename):
            html = codecs.open(filename, "r", "utf-8").read()
        else:
            resp = requests.get(url)
            if encoding is None:
                resp.encoding = resp.apparent_encoding
                html = resp.text
            else:
                html = unicode(html, encoding, errors="ignore")
            fp = codecs.open(filename, "w", "utf-8")
            fp.write(html)
            fp.close()
        return html

    url = sys.argv[1]
    html = url_open(url)

    ce = ContentExtractor(alpha=0.1, beta=1.0).fit(html)
    # extract weighted texts
    print "weighted texts (top 10):"
    h = ce.get_weighted_texts()
    for text, weight in sorted(h, key=lambda x:x[1], reverse=True)[:10]:
        print text, weight
    print

    # extract bs4's elements
    print "bs4 elements (top 5):"
    for elem, score in ce.extract_elements(topn=5):
        print elem.name, elem.attrs, score
    print

    # extract content text (this is not robust, please use "weighted texts")
    print "top-1 text:"
    print ce.extract_text(deliminator=u"\n")
    print

    # extract images from topn elements and its confidences.
    print "content images (in top 10 elements)"
    for src, score in ce.extract_images(topn=3):
        print src, score
