import React, { useEffect, useState } from 'react'
import { AccessibilityInfo, AppState, StyleSheet, Text, View } from 'react-native'
import { useIsFocused } from '@react-navigation/native'
import Animated from 'react-native-reanimated'
import { useColors } from './ui'

const pulse = { '0%': { opacity: .5 }, '50%': { opacity: 1 }, '100%': { opacity: .5 } }
type Kind = 'student' | 'screening' | 'detail' | 'agreement' | 'choice' | 'field' | 'image' | 'heading'

export default function LoadingSkeleton({ kind = 'screening', count = 2, label: customLabel }: { kind?: Kind; count?: number; label?: string }) {
  const c=useColors(), focused=useIsFocused()
  // Begin static until the accessibility preference is known.
  const [reduced,setReduced]=useState(true),[active,setActive]=useState(AppState.currentState==='active')
  useEffect(()=>{
    let mounted=true
    AccessibilityInfo.isReduceMotionEnabled().then(value=>{if(mounted)setReduced(value)}).catch(()=>{})
    const preference=AccessibilityInfo.addEventListener('reduceMotionChanged',setReduced)
    const appState=AppState.addEventListener('change',value=>setActive(value==='active'))
    return ()=>{mounted=false;preference.remove();appState.remove()}
  },[])
  const label=customLabel||(kind==='student'?'Loading students':kind==='agreement'?'Loading agreement':kind==='image'?'Loading handwriting image':'Loading records')
  const single=['detail','agreement','field','image','heading'].includes(kind)
  const block=(width:number|`${number}%`,height=14)=> <View style={{width,height,borderRadius:4,backgroundColor:c.skeleton}}/>
  return <View accessible accessibilityLabel={label} accessibilityRole="progressbar" accessibilityLiveRegion="polite" accessibilityState={{busy:true}} style={s.container}>
    <Text style={[s.label,{color:c.muted}]}>{label}…</Text>
    <Animated.View accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
      style={{borderRadius:16,overflow:'hidden',opacity:.75,animationName:!reduced&&active&&focused?pulse:undefined,animationDuration:1400,animationIterationCount:'infinite',animationTimingFunction:'ease-in-out'}}>
      {Array.from({length:single?1:count},(_,index)=><View key={index} style={[s.placeholder,{backgroundColor:c.surface,borderColor:c.border,borderBottomWidth:!single&&index<count-1?1:0},(kind==='field'||kind==='heading')&&{padding:0},kind==='choice'&&{minHeight:80}]}>
        {kind==='field'?block('100%',52):kind==='heading'?<>{block('72%',26)}{block('38%',14)}</>:kind==='image'?<>{block('100%',300)}{block('42%',12)}</>:kind==='choice'?<View style={s.student}><View style={{flex:1,gap:10}}>{block('66%',16)}{block('46%',12)}</View><View style={{width:24,height:24,borderRadius:12,backgroundColor:c.skeleton}}/></View>:kind==='student'?<View style={s.student}><View style={{width:40,height:40,borderRadius:20,backgroundColor:c.skeleton}}/><View style={{flex:1,gap:10}}>{block('76%',16)}{block('38%',12)}</View></View>:
          <>{kind==='screening'?<View style={s.student}><View style={{width:36,height:36,borderRadius:18,backgroundColor:c.skeleton}}/><View style={{flex:1,gap:10}}>{block('76%',16)}{block('66%',12)}</View></View>:<>{block('64%',18)}{block('42%')}</>}
            {kind==='screening'?<View style={s.badges}>{block(86,26)}{block(96,26)}</View>:<View style={{gap:14,paddingVertical:12}}>{block('94%')}{block('86%')}{block('90%')}{block('62%')}</View>}
            {block('32%',12)}
            {kind==='detail'&&<View style={{gap:14,paddingTop:24}}>{block('54%',18)}{block('90%')}{block('72%')}</View>}
          </>}
      </View>)}
    </Animated.View>
  </View>
}
const s=StyleSheet.create({
  container:{gap:12},label:{fontSize:13,lineHeight:20},
  placeholder:{padding:16,gap:12},student:{flexDirection:'row',alignItems:'center',gap:14,minHeight:48},
  badges:{flexDirection:'row',flexWrap:'wrap',gap:8},
})
