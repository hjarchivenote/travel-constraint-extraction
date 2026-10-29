// Accepts a live-session presentation or a standalone Artifact Tool presentation.
// Scores are read from the completed experiment, never written by hand.
import fs from 'node:fs/promises';
import path from 'node:path';

export async function buildSlides(presentation, root, chartFont) {
  const result=JSON.parse(await fs.readFile(path.join(root,'experiments/results/comparison.json'),'utf8'));
  const m=result.metrics, lo=m.small_lora, base=m.small_baseline;
  const C={bg:'#F6F6EF',ink:'#18362F',teal:'#245D51',muted:'#5F7168',line:'#D6DDD3',soft:'#E5EDE3'};
  presentation.theme.defaultFont='Arial';
  if(presentation.slides.items.length) throw new Error('Build requires an empty presentation.');
  const addText=(slide,text,x,y,w,h,size=26,bold=false,color=C.ink)=>{
    const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    s.text=text;s.text.style={typeface:'Arial',fontSize:size,bold,color}; return s;
  };
  const rule=(slide,y)=>slide.shapes.add({geometry:'rect',position:{left:64,top:y,width:1152,height:1},fill:C.line,line:{fill:'none',width:0}});
  const newSlide=(title,n)=>{
    const s=presentation.slides.add({width:1280,height:720});s.background.fill=C.bg;
    addText(s,'RECENT AREAS OF AI  /  HYOJIN LEE',64,28,1020,25,14,true,C.muted);
    addText(s,String(n).padStart(2,'0'),1152,28,64,25,14,true,C.muted);
    if(title)addText(s,title,64,77,1152,68,44,true);
    rule(s,666);addText(s,'Travel Constraint Extraction · 2026',64,679,1152,24,14,false,C.muted);return s;
  };
  const addTable=(slide,values,x,y,width,height,widths,font=24)=>{
    const t=slide.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,columnWidths:widths,values});
    t.borders.assign({style:'solid',fill:C.line,width:.7});
    for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){
      const cell=t.getCell(r,c);cell.fill=r===0?C.teal:(r%2===0?C.soft:C.bg);
      cell.text.style={typeface:'Arial',fontSize:r===0?font-2:font,bold:r===0,color:r===0?'#FFFFFF':C.ink};
    }
    return t;
  };
  const notes=[];
  const note=(slide,text,sources)=>{slide.speakerNotes.text=text+'\n\nSources: '+sources;notes.push(text);};

  let s=newSlide('',1);
  addText(s,'Travel Constraint\nExtraction',64,146,1130,188,74,true);
  addText(s,'Fine-tuning a small Transformer to understand\nchanges to a London itinerary',68,368,1120,100,32,false,C.teal);
  rule(s,515);
  addText(s,'A 400-example dataset for structured extraction',68,548,1120,48,26);
  note(s,'My project extracts travel constraints from English requests. A traveler might ask to keep a gallery visit, return earlier, and choose an indoor activity if it rains. The main task is understanding these instructions and producing structured JSON. I compare a small model before and after LoRA fine-tuning with a larger model using two examples. The itinerary interface makes the extracted conditions visible. It is a demonstration rather than a route optimizer.',
       'Project report; https://arxiv.org/abs/2412.15115; https://arxiv.org/abs/2106.09685');

  s=newSlide('Task and output contract',2);
  addText(s,'“Keep the gallery. Be back by 19:00.\nI would prefer less walking.”',64,166,1152,94,33,false,C.teal);
  addTable(s,[['Meaning','Structured output','Priority'],['Keep the gallery','Include the resolved place','Hard'],['Return by 19:00','hotel_return <= 19:00','Hard'],['Less walking','walking_amount: minimize','Soft']],64,287,1152,260,[345,587,220],25);
  addText(s,'Missing time or walking scope requires clarification',64,580,1152,45,26,true);
  note(s,'The input includes a reference itinerary, so the model can resolve phrases such as the gallery or the original return time. Each extracted item has a type, target, operator, value, priority, clarification flag, and weather condition. Direct instructions are hard requirements. Prefer indicates a soft preference. Less walking does not imply a numeric limit. If a time or walking scope is missing, the model should preserve that uncertainty instead of inventing an answer.',
       'src/travel_constraints/contract.py; src/travel_constraints/output_schema.json. Table is illustrative, not a measured prediction.');

  s=newSlide('Data and LoRA training',3);
  addText(s,'400 examples',64,164,520,72,50,true,C.teal);
  addText(s,'280 train / 40 validation / 80 test',64,243,1152,45,29);
  addText(s,'100 scenarios × 4 paraphrases, grouped before splitting',64,296,1152,45,26);
  addTable(s,[['Approach','Model and adaptation'],['Small baseline','Qwen2.5-0.5B, zero-shot'],['Fine-tuned small model','Same 0.5B + LoRA, rank 8, 840 steps'],['Larger comparison','Qwen2.5-7B, 4-bit, two training examples']],64,364,1152,216,[345,807],24);
  addText(s,'AI-reviewed synthetic labels: zero human-verified records',64,607,1152,35,23,true,C.muted);
  note(s,'The dataset has one hundred reference scenarios and four paraphrases per scenario. Splitting by scenario keeps all four together. Separate wording pools remove identical request text across splits, although the task families and templates still repeat. The labels were AI-reviewed and checked automatically; none are marked human-verified. LoRA trains seven hundred thirty-three thousand parameters in the last four layers. The final CPU run completed three epochs after a GPU stability failure. Test examples were not used for training or prompt selection.',
       'data/metadata.json; data/splits.json; experiments/training_run.json; https://arxiv.org/abs/2106.09685');

  s=newSlide('Held-out extraction results',4);
  const keys=['small_baseline','small_lora','large_fewshot'];
  const chart=s.charts.add('bar',{
    position:{left:64,top:152,width:1152,height:293},categories:['0.5B baseline','0.5B + LoRA','7B two-shot'],
    series:[{name:'Content F1 (rounded to 3 decimals)',values:keys.map(k=>Number(m[k].f1.toFixed(3))),fill:C.teal,points:[{idx:0,fill:'#96AA9C'},{idx:1,fill:C.teal},{idx:2,fill:'#B7947D'}]}],
    barOptions:{direction:'column',grouping:'clustered',gapWidth:140},hasLegend:false,
    yAxis:{min:0,max:1,majorUnit:.25,numberFormatCode:'0.00',textStyle:{fontSize:17,fill:C.muted},majorGridlines:{fill:C.line,width:1}},
    xAxis:{textStyle:{fontSize:21,fill:C.ink},line:{fill:C.line,width:1}},
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.000',textStyle:{fontSize:22,bold:true,fill:C.ink}},
    chartFill:C.bg,plotAreaFill:C.bg
  });if(chartFont)chartFont(chart,{fontFamily:'Arial'});
  addTable(s,[['Approach','Exact records','Valid JSON'],...keys.map((k,i)=>[['0.5B baseline','0.5B + LoRA','7B two-shot'][i],`${Math.round(m[k].exact_record_accuracy*80)} / 80`,`${(m[k].schema_validity_rate*100).toFixed(1)}%`])],64,450,1152,174,[500,326,326],22);
  addText(s,'80 inputs in 20 groups. Strict JSON without repair. Different quantization and prompting.',64,634,1152,25,15,false,C.muted);
  note(s,`All three models received the same eighty held-out inputs and output schema. Content F1 requires matching the operator, value, and condition, while priority is scored separately. LoRA achieved F1 ${lo.f1.toFixed(3)}, compared with ${base.f1.toFixed(3)} for the small baseline and ${m.large_fewshot.f1.toFixed(3)} for the larger model. It produced ${Math.round(lo.exact_record_accuracy*80)} fully correct records out of eighty. Strict schema failures count as empty extractions. These scores describe a small synthetic benchmark. The larger model also differs in quantization and prompting, so this does not isolate parameter count.`,
       'experiments/protocol.json; experiments/results/comparison.json. F1 is constraint-content micro F1. Chart values are rounded to three decimals; full precision remains in the JSON. See report for cluster bootstrap intervals.');

  s=newSlide('Conditional London demonstration',5);
  const bytes=await fs.readFile(path.join(root,'docs/images/conditions.png'));
  s.images.add({blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),contentType:'image/png',alt:'Actual validation prediction displayed as six extracted conditions',fit:'contain',position:{left:64,top:161,width:738,height:449}});
  addText(s,'Forecast or simulation',841,181,359,45,27,true,C.teal);
  addText(s,'Rain\nReplace the outdoor walk\nwith a book-cafe category',841,256,359,118,25);
  addText(s,'Dry\nKeep the planned walk',841,396,359,86,25);
  addText(s,'Unknown\nKeep both branches pending',841,502,359,86,25);
  addText(s,'Actual saved validation output. Live mode uses the published LoRA adapter.',64,632,1152,26,16,false,C.muted);
  note(s,'The interface displays an actual saved validation prediction, separate from the test set. It can also run the local LoRA model on edited text. Open-Meteo supplies London forecasts. The planner activates the rainy or dry branch, and keeps both pending when forecast coverage is missing. Simulated weather is labeled. Place candidates use attributed OpenStreetMap coordinates. Opening hours, walking routes, and business availability are not verified. The demo shows how structured language output can support a downstream application.',
       'demo/saved_examples.json; docs/images/conditions.png; https://open-meteo.com/en/docs/ecmwf-api; https://www.openstreetmap.org/copyright. Forecast: Open-Meteo / ECMWF, CC BY 4.0. Place data: © OpenStreetMap contributors, ODbL.');

  s=newSlide('Limitations and next steps',6);
  addText(s,`${lo.f1.toFixed(3)} F1 after LoRA fine-tuning`,64,170,1152,72,44,true,C.teal);
  addText(s,'Measured on a controlled synthetic test set',64,249,1152,48,28);
  const lines=[['Remaining model errors','Walking scope, time operators, and missed conditions'],['Next evaluation','Human-annotated requests across more scenarios'],['Application boundary','Illustrative edits with unverified routes and availability']];
  for(let i=0;i<lines.length;i++){
    let y=330+i*82;addText(s,lines[i][0],64,y,324,40,24,true);addText(s,lines[i][1],408,y,808,65,25);
  }
  addText(s,'github.com/hjarchivenote/travel-constraint-extraction',64,612,1152,35,23,false,C.teal);
  note(s,'The main result is a reproducible comparison, not a claim that travel planning is solved. The model still makes important mistakes with walking scope and time relations. The next step would be an independently annotated set of real requests and repeated training seeds. AI assistance was used for code, synthetic labels, experiments, and documentation, and is disclosed in the report. The repository includes the dataset, adapter, raw predictions, evaluation code, and runnable demo so that the result can be inspected.',
       'experiments/results/error_analysis.json; project report, section 7.');
  const words=notes.join(' ').trim().split(/\s+/).length;
  await fs.writeFile(path.join(root,'docs/presentation_script.md'),'# Presentation script\n\nApproximate spoken length: '+words+' words. Rehearse with a timer; target 4:30, maximum 5:00.\n\n'+notes.map((x,i)=>`## Slide ${i+1}\n\n${x}\n`).join('\n'));
  return {slides:presentation.slides.items.length,spokenWords:words,requiredNativeTableOwnerSlides:[2,3,4],requiredNativeChartOwnerSlides:[4]};
}
