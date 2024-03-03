
var result = document.getElementById('result');
function startConverting () {

if('webkitSpeechRecognition' in window) {
    var speechRecognizer = new webkitSpeechRecognition();
    speechRecognizer.continuous = true;
    speechRecognizer.interimResults = true;
    speechRecognizer.lang = 'en-US';
    speechRecognizer.start();
    document.getElementById("mic").style.display = "block";
    var finalTranscripts = '';

    speechRecognizer.onresult = function(event) {
        var interimTranscripts = '';
        for(var i = event.resultIndex; i < event.results.length; i++){
            var transcript = event.results[i][0].transcript;
            transcript.replace("\n", "<br>");
            if(event.results[i].isFinal) {
                finalTranscripts += transcript;
            }else{
                interimTranscripts += transcript;
            }
        }
        result.innerHTML = finalTranscripts + '<span style="color: #999">' + interimTranscripts + '</span>';
    };
    speechRecognizer.onerror = function (event) {

    };
}else {
    result.innerHTML = 'Your browser is not supported. Please download Google chrome or Update your Google chrome!!';
}	
}
stopConverting = function(){
    var speechRecognizer = new webkitSpeechRecognition();
    speechRecognizer.continuous = true;
    speechRecognizer.interimResults = true;
    speechRecognizer.lang = 'en-US';
    speechRecognizer.stop();
    document.getElementById("mic").style.display = "none";
}


// // grab the UI elements to work with
// const textEl = document.getElementById('text');
// const speakEl = document.getElementById('speak');

// // click handler
// speakE2.addEventListener('click', speakText);

// function speakText() {
//   // stop any speaking in progress
//   window.speechSynthesis.cancel();
  
//   // speak text
//   const text = textEl.value();
//   const utterance = new SpeechSynthesisUtterance(text);
//   window.speechSynthesis.speak(utterance);
// }


// user_data script