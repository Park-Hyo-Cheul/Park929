from cdss.medqna.pubmed_client import PubMedClient


def test_parse_search_ids():
    payload = {"esearchresult": {"idlist": ["123", "456"]}}
    assert PubMedClient.parse_search_ids(payload) == ["123", "456"]


def test_parse_abstracts_xml_extracts_core_fields():
    xml_payload = """
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>12345</PMID>
          <Article>
            <ArticleTitle>Test Title</ArticleTitle>
            <Abstract>
              <AbstractText>Line one.</AbstractText>
              <AbstractText>Line two.</AbstractText>
            </Abstract>
            <Journal>
              <JournalIssue>
                <PubDate><Year>2024</Year></PubDate>
              </JournalIssue>
            </Journal>
          </Article>
        </MedlineCitation>
      </PubmedArticle>
    </PubmedArticleSet>
    """
    items = PubMedClient.parse_abstracts_xml(xml_payload)
    assert len(items) == 1
    assert items[0].title == "Test Title"
    assert "Line one." in items[0].summary
    assert items[0].year == 2024
    assert items[0].url == "https://pubmed.ncbi.nlm.nih.gov/12345/"
