let current_word;
let current_phrases=[];
let target_word;
let phrase_pointer=0;
let points = 0;
let current_points;
function load() {


	 /*YaGames.init()

    .then((ysdk) => {

        
        document.getElementById("lang").textContent=ysdk.environment.i18n.lang;
        ysdk.features.LoadingAPI?.ready();
        while (document.getElementById("lang").textContent == "Language") {
            console.log("Language loading");
            sleep(20);
        }
        loadFunction();

    })

    .catch(console.error);*/
    document.getElementById("lang").textContent="ru";


    document.getElementById("game_lang").textContent=document.getElementById("lang").textContent;
    loadFunction();

    
}

function setGoal(phraseJson) {
    document.getElementById("goal").innerHTML=setText("Ваша цель — ","Your goal is ")+ "<i><b>...</b></i>";
    var filtered_words=Object.keys(Object.fromEntries(Object.entries(phraseJson.words_occurrences).filter(([k,v]) => v>1)));
    const userAction = 
     async () => {
  var randWord= filtered_words[Math.floor((Math.random()*filtered_words.length))];
  const r = await fetch('http://185.22.62.80:8000/possibleGoals/'+randWord+'/2');
  j = await r.json();
  target_word= j[Math.floor((Math.random()*j.length))];
  console.log("Set target word to "+target_word);
  document.getElementById("goal").innerHTML=setText("Ваша цель — ","Your goal is ")+ "<i><b>"+ target_word+"</b></i>";

}
userAction();
  
}

function nextPhrases(word) {
    current_points++;
    document.getElementById("prev_phrase").disabled=false;
    document.getElementById("next_phrase").disabled=false;
    prev_id=current_phrases[phrase_pointer].id;
    console.log("Previous id is "+prev_id);
    current_phrases=[];
    phrase_pointer=0;
    console.log("You summoned "+word);
    const userAction = 
     async () => {
  const response = await fetch('http://185.22.62.80:8000/phraseIds/'+word);
  const ids = await response.json(); 
  console.log(ids);
  for (const id of ids) {
    const resp = await fetch('http://185.22.62.80:8000/phrase/'+id);
    current_phrases.push(await resp.json()); 
  }
  console.log(current_phrases);
  console.log(phrase_pointer);
  console.log("New phrase id is "+ current_phrases[phrase_pointer].id)
  if (current_phrases[phrase_pointer].id == prev_id) phrase_pointer++;
  drawPhrase(current_phrases[phrase_pointer]);
}

userAction();
}

function drawPhrase(phraseJson) {
    var d = document.getElementById("phrase");
    d.style.fontFamily= "Lucida Console";
    d.style.textAlign= "justify";
    d.textContent=phraseJson.phrase;
    var filtered_words=Object.keys(Object.fromEntries(Object.entries(phraseJson.words_occurrences).filter(([k,v]) => v>1)));

  for (const element of filtered_words) {
    const r = new RegExp("( |^)"+element);
  d.innerHTML=d.innerHTML.replace(r,'$1<a onclick=nextPhrases("'+element+'")>'+d.innerHTML.match(element)+"</a>");
}
a = document.createElement("p");
a.style.textAlign= "center";
a.id="author";
a.innerHTML=phraseJson.source_author+", <i>"+phraseJson.source_name+"</i>";
d.appendChild(a);
if (phraseJson.lemmas.includes(target_word)) {
     points += Math.max(100+(3-current_points)*10,0);
     current_points=0;
     const userAction = 
     async () => {await setGoal(phraseJson);
    putAlert("Вы выиграли! Подбираем вам новую цель. Сейчас у вас "+ points +" очков за эту игру.","You won. Shortly we'll find you a new goal. You currently have "+points+" points for that game.");
}
userAction();
}

}


function loadFunction() {
    
	


	 const userAction = 
     async () => {
       

  p0=document.createElement("p");
  p0.id="text";
  p0.style.display="table-row";
  p0.style.height="auto";


  

  d=document.createElement("div");
  d.id="phrase";
  d.style.display="inline-block";
  d.style.overflow="hidden";
  p0.appendChild(d);

  p01=document.createElement("p");
  p01.id="menu";
  p01.style.display="table";
  p01.style.height="auto";
  //p01.style.tableLayout="fixed";
  p01.style.width="100%";


  p1=document.createElement("p");
  p1.id="arrows";
  p1.style.display="table-row";
  p1.style.height="auto";
  p1.style.width="100%";

  b1=document.createElement("button");
  b1.id="prev_phrase";
  b1.textContent="<-";
  b1.style.display="table-cell";

  b1.onclick=function() {if (phrase_pointer == 0) phrase_pointer=current_phrases.length-1; else phrase_pointer--; drawPhrase(current_phrases[phrase_pointer])};
  b1.disabled=true;
  //document.getElementById("game").appendChild(b1);
  p1.appendChild(b1);

  b2=document.createElement("button");
  b2.disabled=true;
  b2.id="next_phrase";
  b2.textContent="->";
  b2.style.marginRight="0px";
  b2.style.display="table-cell";
  
  b2.onclick=function() {if (phrase_pointer == current_phrases.length-1) phrase_pointer=0; else phrase_pointer++; drawPhrase(current_phrases[phrase_pointer])};
  //document.getElementById("game").appendChild(b2);
  p1.appendChild(b2);

  d1=document.createElement("div");
    d1.id="goal";
    d1.style.display="table-cell";
    d1.style.overflow="hidden";
    d1.style.width="auto";
    d1.style.margin="0px";
    //d1.style.bottom=vh(15);
    //d1.style.left=vw(40);
    //d1.style.height=vh(5);
    p1.appendChild(d1);

  b3=document.createElement("button");
  b3.id="clipboard";
  b3.textContent=setText("Скопировать цитату","Copy to clipboard");
  b3.style.display="table-cell";
  
  b3.onclick=function() {
    var c = current_phrases[phrase_pointer];
    navigator.clipboard.writeText(c.phrase+"\n\n"+c.source_author+", "+c.source_name);};
  p1.appendChild(b3);


  
  b0=document.createElement("button");
  b0.id="newgame";
  b0.textContent=setText("Новая игра","New game");
  b0.style.display="table-cell";
  b0.style.marginRight= 0;
  b0.style.overflow="hidden";
  b0.onclick=function(){putAlert(setText("Генерируем новую игру","Preparing new game"));
  points = 0;
while (document.getElementById("game").firstChild) {
                    document.getElementById("game").removeChild(document.getElementById("game").lastChild);
            }
            loadFunction()}
  p1.appendChild(b0);

  d0=document.createElement("button");
  d0.id="game_lang_2";
  d0.style.display="table-cell";
  d0.style.marginLeft= 0;
  d0.textContent=document.getElementById("game_lang").textContent;
  d0.onclick=function(){if (d0.textContent=="ru") d0.textContent="en"; else d0.textContent="ru"; document.getElementById("game_lang").textContent=d0.textContent;};
  p1.appendChild(d0);
  
  
  
  document.getElementById("helper").textContent=setText("Помощь","Help");

  /* p2=document.createElement("p");
  p2.id="goal_p";
  p2.style.display="table-row";
  p2.style.height="auto";
  p2.style.width="100%";*/

    

    current_points=0;
    //p2.appendChild(d1);

    document.getElementById("game").appendChild(p0);
    document.getElementById("game").appendChild(p01);
    //p01.appendChild(p2);
    p01.appendChild(p1);

     var phrase;
  do {
  const response = await fetch('http://185.22.62.80:8000/randomPhrase/'+document.getElementById("game_lang").textContent);
  phrase = await response.json(); 

  while(phrase == null) sleep(100);
} while (Object.keys(Object.fromEntries(Object.entries(phrase.words_occurrences).filter(([k,v]) => v>1))).length==0);
  current_phrases=[];
  current_phrases.push(phrase);
  phrase_pointer=0;
  console.log(current_phrases);

  setGoal(phrase);
  


  drawPhrase(phrase);
}

userAction();
               /* YaGames.init()

    .then((ysdk) => {

        // Informing about starting the gameplay.

        ysdk.features.GameplayAPI?.start()


    }); */   
	
	
}

function showHelp() {


/*while (document.getElementById("game").firstChild) {
    				document.getElementById("game").removeChild(document.getElementById("game").lastChild);
    			}*/
	var d= document.createElement("div");
                    d.className=d.className+'alert';
                    d.id='helpstring';

                    d.style.display="block";
                    d.style.margin="0";
                    d.style.textAlign="left";
                    

                    var h1 = document.createElement("h1");
                    h1.textContent=setText("Как играть","How to play");
                    h1.style.fontSize="2vw";
                    h1.style.align="center";
                    h1.style.width="50vw";
                    h1.style.margin="0";
                    d.appendChild(h1);

                    var p1 = document.createElement("p");
                    p1.textContent=setText("Перед вами лабиринт из книжных фраз. Ваша задача — дойти до заданного слова. Каждое слово предложения может вести к новым предложениям с этим словом. Слова, которые куда-то ведут, подчеркнуты и являются ссылками. Переключаться между предложениями с одним словом можно стрелками под фразой. Ваш путь не обязан быть кратчайшим, можно просто ходить и открывать для себя новые книги.","This game is a maze of book quotes. You start with a phrase and need to get to a certain word. Every word in a phrase may lead you to new sentences with it. Words that lead somewhere are underlined hyperlinks. To switch between sentences with a certain word, use arrows under the phrase. Your path doesn't need to be the shortest, you can just wander and discover new books.");
                    d.appendChild(p1);

                    var p2=document.createElement("p");
                    p2.textContent=setText("Доступны предложения на двух языках, русском и английском. Выбрать язык новой игры можно рядом с кнопкой «Новая игра». База предложений будет пополняться.","You can play in two languages, English and Russian. To switch the language, press the language field near the New Game button. More sentences will come soon.");
                    d.appendChild(p2);

                    //help
                    var btn2 = document.createElement("button");
                           //btn.setAttribute("value",i+'_'+j);
                           btn2.className = btn2.className + "button";
                           btn2.textContent=setText("Ага","Ok");
                           btn2.onclick = function() {document.getElementById("helpstring").parentNode.removeChild(document.getElementById("helpstring")); /*loadFunction();*/};
                    d.appendChild(btn2);


                    document.getElementById("game").appendChild(d);

}