from pathlib import Path
from typing import List

from html2text import html2text
from langchain.text_splitter import TokenTextSplitter

from .types import Doc, Text
import fitz
import markdown
from .types import Doc, Text
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.schema import Document
import strip_markdown

def parse_pdf_fitz(path: Path, doc: Doc, chunk_chars: int, overlap: int) -> List[Text]:
    import fitz

    file = fitz.open(path)
    split = ""
    pages: List[str] = []
    texts: List[Text] = []
    for i in range(file.page_count):
        page = file.load_page(i)
        split += page.get_text("text", sort=True)
        pages.append(str(i + 1))
        # split could be so long it needs to be split
        # into multiple chunks. Or it could be so short
        # that it needs to be combined with the next chunk.
        while len(split) > chunk_chars:
            # pretty formatting of pages (e.g. 1-3, 4, 5-7)
            pg = "-".join([pages[0], pages[-1]])
            texts.append(
                Text(
                    text=split[:chunk_chars], name=f"{doc.docname} pages {pg}", doc=doc
                )
            )
            split = split[chunk_chars - overlap :]
            pages = [str(i + 1)]
    if len(split) > overlap:
        pg = "-".join([pages[0], pages[-1]])
        texts.append(
            Text(text=split[:chunk_chars], name=f"{doc.docname} pages {pg}", doc=doc)
        )
    file.close()
    return texts


def parse_pdf(path: Path, doc: Doc, chunk_chars: int, overlap: int) -> List[Text]:
    import pypdf

    pdfFileObj = open(path, "rb")
    pdfReader = pypdf.PdfReader(pdfFileObj)
    split = ""
    pages: List[str] = []
    texts: List[Text] = []
    for i, page in enumerate(pdfReader.pages):
        split += page.extract_text()
        pages.append(str(i + 1))
        # split could be so long it needs to be split
        # into multiple chunks. Or it could be so short
        # that it needs to be combined with the next chunk.
        while len(split) > chunk_chars:
            # pretty formatting of pages (e.g. 1-3, 4, 5-7)
            pg = "-".join([pages[0], pages[-1]])
            texts.append(
                Text(
                    text=split[:chunk_chars], name=f"{doc.docname} pages {pg}", doc=doc
                )
            )
            split = split[chunk_chars - overlap :]
            pages = [str(i + 1)]
    if len(split) > overlap:
        pg = "-".join([pages[0], pages[-1]])
        texts.append(
            Text(text=split[:chunk_chars], name=f"{doc.docname} pages {pg}", doc=doc)
        )
    pdfFileObj.close()
    return texts


def parse_txt(
    path: Path, doc: Doc, chunk_chars: int, overlap: int, html: bool = False
) -> List[Text]:
    try:
        with open(path) as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    if html:
        text = html2text(text)
    # yo, no idea why but the texts are not split correctly
    text_splitter = TokenTextSplitter(chunk_size=chunk_chars, chunk_overlap=overlap)
    raw_texts = text_splitter.split_text(text)
    texts = [
        Text(text=t, name=f"{doc.docname} chunk {i}", doc=doc)
        for i, t in enumerate(raw_texts)
    ]
    return texts


def parse_code_txt(path: Path, doc: Doc, chunk_chars: int, overlap: int) -> List[Text]:
    """Parse a document into chunks, based on line numbers (for code)."""

    split = ""
    texts: List[Text] = []
    last_line = 0

    with open(path) as f:
        for i, line in enumerate(f):
            split += line
            if len(split) > chunk_chars:
                texts.append(
                    Text(
                        text=split[:chunk_chars],
                        name=f"{doc.docname} lines {last_line}-{i}",
                        doc=doc,
                    )
                )
                split = split[chunk_chars - overlap :]
                last_line = i
    if len(split) > overlap:
        texts.append(
            Text(
                text=split[:chunk_chars],
                name=f"{doc.docname} lines {last_line}-{i}",
                doc=doc,
            )
        )
    return texts


def read_doc(
    path: Path,
    doc: Doc,
    chunk_chars: int = 3000,
    overlap: int = 100,
    force_pypdf: bool = False,
) -> List[Text]:
    """Parse a document into chunks."""
    str_path = str(path)
    if str_path.endswith(".pdf"):
        if force_pypdf:
            return parse_pdf(path, doc, chunk_chars, overlap)
        try:
            return parse_pdf_fitz(path, doc, chunk_chars, overlap)
        except ImportError:
            return parse_pdf(path, doc, chunk_chars, overlap)
    elif str_path.endswith(".txt"):
        return parse_txt(path, doc, chunk_chars, overlap)
    elif str_path.endswith(".html"):
        return parse_txt(path, doc, chunk_chars, overlap, html=True)
    elif str_path.endswith(".md"):
        return parse_md(path, doc, chunk_chars, overlap)        
    else:
        return parse_code_txt(path, doc, chunk_chars, overlap)


def split_text(text, max_length):
    chunks = []
    while len(text) > max_length:
        # Find the nearest "\n" character within the max_length range
        split_index = text.rfind("\n", 0, max_length)
        if split_index == -1:
            # If no "\n" found, split at max_length
            split_index = max_length
        chunks.append(text[:split_index].strip())
        text = text[split_index:]
    if text:
        chunks.append(text.strip())
    return chunks

def parse_md(
    path: Path, doc: Doc, chunk_chars: int, overlap: int) -> List[Text]:
    with open(path, 'r', encoding='utf-8') as f:
        markdown_document = f.read()
    headers_to_split_on = [
        ("#", "#"),
        ("##", "##"),
        ("###", "###"),
        ("####", "####"),
    ]
    print("chunks=================",chunk_chars)
    # MD splits
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(markdown_document)

    for d in md_header_splits:
        d.page_content = strip_markdown.strip_markdown(d.page_content)
        for k in d.metadata:
            d.metadata[k] = strip_markdown.strip_markdown(d.metadata[k])

    print("==md_header_splits", md_header_splits)

    # Step 1: 获取段落等级 1，2，3，4
    header_level = []
    print("共有{}个段落".format(len(md_header_splits)))
    for t in md_header_splits:
        print(max(t.metadata.keys()))
        header_level.append(len(max(t.metadata.keys())))
    print("header_level[本段内容对应的级数]", header_level)  # 例如[1, 2, 2, 3, 4, 3, 4, 3, 4]

    # Step 2: 获取每一个位置最长递增子序列的长度，并找到对应的索引位置
    header_max_idx = []
    for i in range(len(header_level) - 1):
        for j in range(i + 1, len(header_level)):
            if (header_level[j] > header_level[i]):
                if j == len(header_level) - 1:
                    header_max_idx.append(j + 1)
            else:
                header_max_idx.append(j)
                break
    header_max_idx.append(len(header_level))
    print("header_max_idx[本段内容树遍历停止索引]", header_max_idx)

    # Step 3: 前缀和获取文本总长度
    pre_sum = [0]
    cur_sum = 0
    for i, t in enumerate(md_header_splits):
        cur_sum += len(t.page_content)
        pre_sum.append(cur_sum)
    print("pre_sum[文本内容长度前缀和]", pre_sum)

    # Step 4: 计算合并拆分动作发生点 -1:正常 -2：拆分 num_idx:从当前位置合并到一个索引
    dongzuo = []
    for i, cur_level in enumerate(header_level):
        cur_words = pre_sum[header_max_idx[i]] - pre_sum[i]
        if cur_words > chunk_chars:
            if pre_sum[i + 1] - pre_sum[i] > chunk_chars:  # 当前段文字
                dongzuo.append(-2)
            else:
                dongzuo.append(-1)
        else:
            if header_max_idx[i] - i <= 1:
                dongzuo.append(-1)
            else:
                dongzuo.append(header_max_idx[i])
    print("dongzuo[动作]", dongzuo)

    # Step 5: 进行处理合并拆分
    texts = []
    idx = 0
    mergeFlags = []
    headers_metadata = []
    while idx <= len(header_level) - 1:
        if (dongzuo[idx]) == -1:
            # 获取最后等级 header
            last_level_header = max(md_header_splits[idx].metadata.keys())
            last_level_text = md_header_splits[idx].metadata[last_level_header]
            texts.append(Text(text=last_level_header +' ' + last_level_text + '\n' + md_header_splits[idx].page_content,
                              name=f"{doc.docname},chunk {last_level_header}", doc=doc))
            idx += 1
            mergeFlags.append(-1)
        elif (dongzuo[idx]) == -2:
            last_level_header = max(
                md_header_splits[idx].metadata.keys())
            last_level_text = md_header_splits[idx].metadata[last_level_header]
            content_chunks = split_text(md_header_splits[idx].page_content, chunk_chars)
            for i, chunk in enumerate(content_chunks):
                name = f"{doc.docname},chunk {last_level_header} part {i + 1}"
                texts.append(Text(text=last_level_header + ' ' + last_level_text + '\n' + chunk, name=name, doc=doc))
            idx += 1
            mergeFlags.append(0)
        else:
            cur_text = ""
            for i in range(idx, dongzuo[idx]):
                # 获取最后等级 header
                last_level_header = max(md_header_splits[i].metadata.keys())
                last_level_text = md_header_splits[i].metadata[last_level_header]
                cur_text += last_level_header + ' ' + last_level_text + '\n' + md_header_splits[i].page_content
                if (i == idx):
                    name = f"{doc.docname},chunk {last_level_header}"
            texts.append(Text(text=cur_text, name=name, doc=doc))
            idx = dongzuo[idx]
            mergeFlags.append(-1)
        #headers_metadata.append()

    # Step 6: 进行再次合并处理 -1 可合并,-2不可参与合并
    print("再次合并处理标志",mergeFlags)
    texts2 = []
    max_length = chunk_chars
    merged = []
    buffer = []
    length = 0
    num = 0
    for i, mergeFlag in enumerate(mergeFlags):
        if mergeFlag == -1:
            if length + len(texts[i].text) > max_length and len(texts) !=1:
                merged.append(" ".join(buffer))
                texts2.append(Text(text=merged[num], name=texts[i].name, doc=doc))
                num = num + 1
                buffer = []
                buffer.append(texts[i].text)
                length = 0
            else:
                buffer.append(texts[i].text)
                length += len(texts[i].text)
        if mergeFlag == -2 or i == len(mergeFlags) - 1:
            merged.append(" ".join(buffer))
            texts2.append(Text(text=merged[num], name=texts[i].name, doc=doc))
            num = num + 1
            buffer = []
            length = 0

    print("->merged", merged)
    print("->texts", texts)
    print("->texts2", texts2)
    return texts2
