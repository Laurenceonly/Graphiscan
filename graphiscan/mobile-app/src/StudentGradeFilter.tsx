import React, {useRef, useState} from 'react'
import {Keyboard, Modal, Pressable, Text, View, useWindowDimensions} from 'react-native'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import {styles, useColors} from './ui'

const choices=[{value:'',label:'All grades'},...[1,2,3].map(value=>({value:String(value),label:'Grade '+value}))]

export default function StudentGradeFilter({value,onChange}:{value:string;onChange:(value:string)=>void}){
  const c=useColors(),anchor=useRef<React.ComponentRef<typeof View>>(null),{width,height}=useWindowDimensions()
  const [position,setPosition]=useState<{left:number;top:number}|null>(null)
  function open(){Keyboard.dismiss();anchor.current?.measureInWindow((x,y,w,h)=>setPosition({left:Math.max(12,Math.min(x+w-200,width-212)),top:Math.min(y+h+6,height-236)}))}
  return <>
    <View ref={anchor} collapsable={false}>
      <Pressable accessibilityRole="button" accessibilityLabel={'Filter by grade: '+(choices.find(choice=>choice.value===value)?.label||'All grades')} accessibilityState={{expanded:Boolean(position)}} onPress={open}
        style={({pressed})=>({width:52,minHeight:52,alignItems:'center',justifyContent:'center',borderWidth:1,borderColor:value?c.primary:c.border,borderRadius:10,backgroundColor:value?c.soft:c.surface,opacity:pressed?.8:1})}>
        <MaterialIcons name="filter-list" size={24} color={c.primary}/>
      </Pressable>
    </View>
    <Modal visible={Boolean(position)} transparent animationType="none" statusBarTranslucent onRequestClose={()=>setPosition(null)}>
      <View style={{flex:1}}>
        <Pressable accessibilityRole="button" accessibilityLabel="Close grade filter" onPress={()=>setPosition(null)} style={{position:'absolute',inset:0}}/>
        <View accessibilityRole="menu" accessibilityLabel="Grade" style={{position:'absolute',left:position?.left??12,top:position?.top??0,width:200,paddingVertical:4,borderRadius:12,backgroundColor:c.surface,elevation:6}}>
          {choices.map(choice=><Pressable key={choice.value} accessibilityRole="menuitem" accessibilityLabel={choice.label} accessibilityState={{selected:value===choice.value}} onPress={()=>{onChange(choice.value);setPosition(null)}}
            style={({pressed})=>({minHeight:52,paddingHorizontal:16,paddingVertical:12,flexDirection:'row',alignItems:'center',gap:12,backgroundColor:pressed||value===choice.value?c.soft:c.surface})}>
            <Text style={[styles.body,{color:c.text,flex:1}]}>{choice.label}</Text>
            {value===choice.value&&<MaterialIcons name="check" size={20} color={c.primary}/>}
          </Pressable>)}
        </View>
      </View>
    </Modal>
  </>
}
