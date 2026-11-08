"""Patient-facing text. Have a native speaker check the Telugu and Hindi before any real use.
Button titles must be 20 characters or fewer (WhatsApp limit)."""

TEXT = {
    "en": {
        "hello": "Namaste {first} garu, this is Godavari Hospital. Your chest X-ray shows something the doctor wants to check with a CT scan. Checking early is important.",
        "ask": "Please answer 3 quick questions so we can book the right slot.",
        "q": ["Do you smoke or chew tobacco?", "Do you have diabetes (sugar)?", "Have you had a cough for more than 2 weeks?"],
        "yes": "Yes", "no": "No",
        "slot": "We have kept a CT slot for you: Thursday, 10:30 AM, Rs 2,975.",
        "book": "Book this slot", "other": "Another time", "call": "Call me",
        "booked": "Booked. Please bring your X-ray report. We will remind you a day before.",
        "other_sent": "Our team will send you two more slot options shortly.",
        "callback": "Our care team will call you within 24 hours.",
        "done": "Thank you for coming. Your report has been sent to your doctor.",
    },
    "hi": {
        "hello": "नमस्ते {first} जी, यह गोदावरी हॉस्पिटल से संदेश है। आपके छाती के एक्स-रे में कुछ दिखा है जिसे डॉक्टर सीटी स्कैन से जाँचना चाहते हैं। जल्दी जाँच कराना ज़रूरी है।",
        "ask": "सही समय बुक करने के लिए 3 छोटे सवालों के जवाब दीजिए।",
        "q": ["क्या आप धूम्रपान करते हैं या तंबाकू खाते हैं?", "क्या आपको डायबिटीज़ (शुगर) है?", "क्या आपको 2 हफ़्ते से ज़्यादा से खाँसी है?"],
        "yes": "हाँ", "no": "नहीं",
        "slot": "आपके लिए सीटी स्लॉट रखा है: गुरुवार, सुबह 10:30, ₹2,975।",
        "book": "स्लॉट बुक करें", "other": "दूसरा समय", "call": "मुझे कॉल करें",
        "booked": "बुक हो गया। अपनी एक्स-रे रिपोर्ट साथ लाएँ। एक दिन पहले याद दिलाएँगे।",
        "other_sent": "हमारी टीम जल्द ही आपको दो और समय भेजेगी।",
        "callback": "हमारी केयर टीम 24 घंटे में आपको कॉल करेगी।",
        "done": "आने के लिए धन्यवाद। आपकी रिपोर्ट डॉक्टर को भेज दी गई है।",
    },
    "te": {
        "hello": "నమస్కారం {first} గారు, ఇది గోదావరి హాస్పిటల్ నుండి సందేశం. మీ ఛాతీ ఎక్స్-రేలో డాక్టర్ గారు సీటీ స్కాన్‌తో పరీక్షించాలనుకునే అంశం కనిపించింది. త్వరగా పరీక్ష చేయించుకోవడం ముఖ్యం.",
        "ask": "సరైన సమయం బుక్ చేయడానికి 3 చిన్న ప్రశ్నలకు జవాబు ఇవ్వండి.",
        "q": ["మీరు పొగ తాగుతారా లేదా పొగాకు నములుతారా?", "మీకు షుగర్ (డయాబెటిస్) ఉందా?", "రెండు వారాలకు పైగా దగ్గు ఉందా?"],
        "yes": "అవును", "no": "లేదు",
        "slot": "మీ కోసం సీటీ స్లాట్ ఉంచాము: గురువారం, ఉదయం 10:30, ₹2,975.",
        "book": "స్లాట్ బుక్ చేయండి", "other": "వేరే సమయం", "call": "నాకు కాల్ చేయండి",
        "booked": "బుక్ అయింది. మీ ఎక్స్-రే రిపోర్ట్ తీసుకురండి. ఒక రోజు ముందు గుర్తు చేస్తాము.",
        "other_sent": "మా టీమ్ త్వరలో మరో రెండు సమయాలు పంపిస్తుంది.",
        "callback": "మా కేర్ టీమ్ 24 గంటల్లో మీకు కాల్ చేస్తుంది.",
        "done": "వచ్చినందుకు ధన్యవాదాలు. మీ రిపోర్ట్ డాక్టర్ గారికి పంపించాము.",
    },
}
