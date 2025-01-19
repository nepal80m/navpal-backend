from google.cloud import translate_v2 as translate

def test_translation():
    translator = translate.Client()
    text = "कस्तो नेपाली पाठ चाहियो? तपाईलाई सामान्य जानकारी, साहित्यिक लेख, औपचारिक लेख, वा कुनै विशेष विषयमा नेपालीमा जानकारी चाहिएको छ भने कृपया स्पष्ट पार्नुहोस्। उदाहरणका लागि, म यहाँ एउटा सामान्य पाठ लेख्छु:"
    target = 'en'
    translation = translator.translate(text, target_language=target)
    print(f"Original: {text}")
    print(f"Translated: {translation['translatedText']}")

if __name__ == "__main__":
    test_translation()